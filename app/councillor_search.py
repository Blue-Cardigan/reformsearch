from typing import List, Dict
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import urlparse
import hashlib
import json
from pathlib import Path
from langchain_core.documents import Document

from tools.google_tool import search_google
from tools.logger import logger

@dataclass
class Councillor:
    first_name: str
    last_name: str
    council: str

    def generate_search_queries(self) -> List[dict]:
        """Generate investigative search patterns for the councillor."""
        full_name = f"{self.first_name} {self.last_name}"
        
        # Structured search queries with context
        queries = [
            {
                "query": f'"{full_name}" councillor {self.council}',
                "category": "basic_info"
            },
            # Political affiliations and changes
            {
                "query": f'"{full_name}" {self.council} party OR conservative OR labour OR independent',
                "category": "political"
            },
            # Voting records and decisions
            {
                "query": f'"{full_name}" {self.council} vote OR decision OR meeting minutes',
                "category": "voting"
            },
            # Business interests and conflicts
            {
                "query": f'"{full_name}" {self.council} business OR company OR director OR interest',
                "category": "business_interests"
            },
            # Public statements and controversies
            {
                "query": f'"{full_name}" {self.council} controversy OR investigation OR complaint',
                "category": "controversy"
            },
            # Social media presence
            {
                "query": f'"{full_name}" {self.council} X OR facebook OR linkedin',
                "category": "social_media"
            }
        ]
        return queries

class CouncillorSearcher:
    def __init__(self, councillors_file: str = "data/councillors.json"):
        self.councillors = self._load_councillors(councillors_file)
        self.results_cache = {}
        # Store baseline results to filter out later
        self.baseline_results = {}

    def _load_councillors(self, file_path: str) -> List[Councillor]:
        """Load and parse councillors from JSON file."""
        try:
            # Use Path for cross-platform compatibility
            path = Path(file_path)
            if not path.exists():
                logger.error(f"Councillors file not found at: {path.absolute()}")
                return []
                
            with path.open('r') as f:
                data = json.load(f)
                return [
                    Councillor(
                        first_name=c['first name'],
                        last_name=c['last name'],
                        council=c['council']
                    ) for c in data['councillor']
                ]
        except Exception as e:
            logger.error(f"Error loading councillors file: {e}")
            return []

    def search_councillor(self, councillor: Councillor, results_per_query: int = 5) -> dict:
        """Three-stage search process for a councillor."""
        full_name = f"{councillor.first_name} {councillor.last_name}"
        
        # Stage 1: Social Media Identification
        social_profiles = self.social_media_search(councillor)
        
        # Stage 2: Baseline Search (to be filtered out later)
        baseline_query = f'"{full_name}" {councillor.council}'
        try:
            baseline_results = search_google(baseline_query, top_n=10)
            self.baseline_results[full_name] = {
                doc.metadata['link']: doc for doc in baseline_results
            }
        except Exception as e:
            logger.error(f"Error in baseline search: {e}")
            self.baseline_results[full_name] = {}

        # Stage 3: Keyword-based searches
        keyword_results = self._keyword_search(councillor, results_per_query)
        
        # Combine and filter results
        return self._combine_filtered_results(
            full_name,
            social_profiles,
            keyword_results
        )

    def _keyword_search(self, councillor: Councillor, results_per_query: int) -> dict:
        """Perform keyword-based searches and filter out baseline results."""
        full_name = f"{councillor.first_name} {councillor.last_name}"
        
        # Define targeted keywords for investigation
        keywords = {
            "business_interests": [
                "companies house", "company director",
                "property developer", "consultant"
            ],
            "controversy": [
                "tommy robinson", "arrested", "protest", "immigrant", "far right",
                "investigation", "complaint", "misconduct", "holocaust", "deport"
            ]
        }
        
        results = {category: [] for category in keywords.keys()}
        
        for category, keyword_list in keywords.items():
            for keyword in keyword_list:
                query = f'"{full_name}" {councillor.council} {keyword}'
                try:
                    search_results = search_google(query, top_n=results_per_query)
                    
                    # Filter out baseline results
                    filtered_results = [
                        result for result in search_results
                        if result.metadata['link'] not in self.baseline_results.get(full_name, {})
                    ]
                    
                    results[category].extend(filtered_results)
                    
                except Exception as e:
                    logger.error(f"Error searching {category} with keyword '{keyword}': {e}")
                    continue
        
        return results

    def _combine_filtered_results(self, full_name: str, 
                                social_profiles: List[dict], 
                                keyword_results: dict) -> dict:
        """Combine social media profiles and filtered keyword results."""
        combined_results = {
            "basic_info": [],
            "social_media": social_profiles,
            "summary": {}
        }
        
        # Add filtered keyword results
        for category, results in keyword_results.items():
            combined_results[category] = results
        
        # Generate summary
        combined_results["summary"] = self._generate_summary(combined_results)
        
        return combined_results

    def _generate_summary(self, results: dict) -> dict:
        """Generate a summary of key findings."""
        summary = {
            "total_results": sum(len(results[cat]) for cat in results if cat != "summary"),
            "potential_interests": self._extract_business_interests(results["business_interests"]),
            "controversy_count": len(results["controversy"]),
            "has_social_media": bool(results["social_media"]),
        }
        return summary

    def save_results(self, results: dict, output_file: str = "councillor_results.json"):
        """Save search results to a JSON file with improved structure."""
        formatted_results = {}
        
        for councillor_name, categories in results.items():
            formatted_results[councillor_name] = {
                "categories": {},
                "summary": categories["summary"]
            }
            
            # Format each category's results
            for category, documents in categories.items():
                if category != "summary":
                    formatted_results[councillor_name]["categories"][category] = [
                        {
                            "title": doc.metadata.get("title", ""),
                            "link": doc.metadata.get("link", ""),
                            "snippet": doc.page_content,
                            "search_time": doc.metadata.get("search_time", ""),
                            "relevance_score": self._calculate_relevance(doc)
                        }
                        for doc in documents
                    ]
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(formatted_results, f, indent=2, ensure_ascii=False)
            logger.info(f"Investigative results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

    def _calculate_relevance(self, doc: Document) -> float:
        """Calculate relevance score based on content and metadata."""
        score = 1.0
        
        # Boost score for official council domains
        if "gov.uk" in doc.metadata.get("link", "").lower():
            score *= 1.5
        
        # Boost for recent content (if date is available)
        if "2024" in doc.page_content or "2023" in doc.page_content:
            score *= 1.2
            
        return round(score, 2)

    def _extract_business_interests(self, documents: List[Document]) -> List[str]:
        """Extract potential business interests from documents."""
        interests = []
        keywords = ["director", "company", "business", "interest", "owner"]
        
        for doc in documents:
            for keyword in keywords:
                if keyword.lower() in doc.page_content.lower():
                    interests.append(doc.metadata.get("title", ""))
                    break
                    
        return list(set(interests))

    def search_all_councillors(self, results_per_query: int = 5) -> dict:
        """Search for all councillors and return results organized by councillor."""
        results = {}
        
        for councillor in self.councillors:
            councillor_key = f"{councillor.first_name} {councillor.last_name}"
            results[councillor_key] = self.search_councillor(councillor, results_per_query)
            
            logger.info(f"Completed investigative search for {councillor_key}")
            
        return results

    def social_media_search(self, councillor: Councillor) -> List[dict]:
        """Focused search for councillor social media profiles."""
        full_name = f"{councillor.first_name} {councillor.last_name}"
        
        social_queries = [
            # LinkedIn - professional profiles
            {
                "query": f'site:linkedin.com/in/ "{full_name}" {councillor.council} councillor',
                "platform": "linkedin"
            },
            # X/X - public statements
            {
                "query": f'site:X.com "{full_name}" {councillor.council}',
                "platform": "X"
            },
            # Facebook - public pages and community engagement
            {
                "query": f'site:facebook.com "{full_name}" councillor {councillor.council}',
                "platform": "facebook"
            }
        ]
        
        social_profiles = []
        
        for query_info in social_queries:
            try:
                results = search_google(query_info["query"], top_n=3)
                
                for result in results:
                    if self._validate_social_profile(result, full_name, query_info["platform"]):
                        social_profiles.append({
                            "platform": query_info["platform"],
                            "url": result.metadata["link"],
                            "title": result.metadata["title"],
                            "confidence_score": self._calculate_profile_confidence(result, full_name)
                        })
                        
            except Exception as e:
                logger.error(f"Error searching {query_info['platform']}: {e}")
                continue
            
        return social_profiles

    def _validate_social_profile(self, result: Document, full_name: str, platform: str) -> bool:
        """Enhanced validation for social media profiles."""
        url = result.metadata["link"].lower()
        title = result.metadata["title"].lower()
        content = result.page_content.lower()
        name_parts = full_name.lower().split()
        
        # More stringent validation rules
        if not all(name in f"{title} {content}" for name in name_parts):
            return False
            
        if platform == "linkedin":
            return ("linkedin.com/in/" in url and 
                    any(name in url.split("/")[-1] for name in name_parts) and
                    ("councillor" in content or "council" in content))
        
        elif platform == "X":
            return ("X.com/" in url and 
                    not "/status/" in url and
                    ("councillor" in title or "cllr" in title))
        
        elif platform == "facebook":
            return ("facebook.com/" in url and 
                    not "/posts/" in url and
                    ("councillor" in title or "official" in title))
        
        return False

    def _calculate_profile_confidence(self, result: Document, full_name: str) -> float:
        """Calculate confidence score for social media profile match."""
        score = 1.0
        content = f"{result.metadata['title']} {result.page_content}".lower()
        name_parts = full_name.lower().split()
        
        # Name matching
        if all(name in content for name in name_parts):
            score *= 1.5
        
        # Role confirmation
        if "councillor" in content or "cllr" in content:
            score *= 1.3
        
        # Location matching
        if councillor.council.lower() in content:
            score *= 1.2
        
        return round(score, 2)

    def update_missing_profiles(self):
        """Update councillor records with missing social media profiles."""
        try:
            # Load existing results
            with open("councillor_results.json", 'r') as f:
                existing_results = json.load(f)
            
            # Initialize searcher
            searcher = CouncillorSearcher()
            updates_made = False
            
            for councillor in searcher.councillors:
                full_name = f"{councillor.first_name} {councillor.last_name}"
                
                # Check if councillor has no social media profiles
                if (full_name in existing_results and 
                    (not existing_results[full_name].get("categories", {}).get("social_media") or 
                     len(existing_results[full_name]["categories"]["social_media"]) == 0)):
                    
                    logger.info(f"Searching social media profiles for {full_name}")
                    
                    # Perform focused social media search
                    social_profiles = self.social_media_search(councillor)
                    
                    if social_profiles:
                        # Update existing results
                        if "categories" not in existing_results[full_name]:
                            existing_results[full_name]["categories"] = {}
                        
                        existing_results[full_name]["categories"]["social_media"] = social_profiles
                        updates_made = True
                        
                        logger.info(f"Found {len(social_profiles)} social media profiles for {full_name}")
            
            # Save updated results if changes were made
            if updates_made:
                with open("councillor_results.json", 'w') as f:
                    json.dump(existing_results, f, indent=2)
                logger.info("Updated councillor_results.json with new social media profiles")
            else:
                logger.info("No new social media profiles found")
                
        except Exception as e:
            logger.error(f"Error updating social media profiles: {e}")

class ResearchTarget:
    def __init__(self, url: str, source_type: str, confidence_score: float, needs_scraping: bool, content_hash: str = "", last_checked: str = ""):
        self.url = url
        self.source_type = source_type
        self.confidence_score = confidence_score
        self.needs_scraping = needs_scraping
        self.content_hash = content_hash
        self.last_checked = last_checked

class InvestigativeResearcher:
    def __init__(self):
        self.research_categories = {
            "statements": {
                "keywords": [
                    "racist", "xenophobic", "discriminatory", "hate", "prejudice",
                    "antisemitic", "islamophobic", "homophobic", "transphobic"
                ],
                "priority": "high"
            },
            "associations": {
                "keywords": [
                    "group", "organization", "association", "member", "affiliate",
                    "supporter", "attended", "spoke", "rally", "protest"
                ],
                "priority": "high"
            },
            "social_media_activity": {
                "keywords": [
                    "shared", "posted", "retweeted", "liked", "commented",
                    "following", "follower"
                ],
                "priority": "medium"
            }
        }

    def generate_research_queries(self, councillor: Councillor) -> List[dict]:
        """Generate comprehensive research queries."""
        full_name = f"{councillor.first_name} {councillor.last_name}"
        queries = []

        # Base queries with site-specific searches
        base_sites = [
            "site:twitter.com", "site:facebook.com", 
            "site:linkedin.com", "site:youtube.com",
            "site:local-news-domain.co.uk"  # Replace with actual local news sites
        ]

        for category, data in self.research_categories.items():
            for keyword in data["keywords"]:
                for site in base_sites:
                    queries.append({
                        "query": f'{site} "{full_name}" {keyword}',
                        "category": category,
                        "priority": data["priority"]
                    })

        # Add council-specific searches
        queries.extend([
            {
                "query": f'site:{councillor.council}.gov.uk "{full_name}"',
                "category": "official_record",
                "priority": "high"
            },
            {
                "query": f'"{full_name}" {councillor.council} complaint OR investigation',
                "category": "complaints",
                "priority": "high"
            }
        ])

        return queries

    def deduplicate_results(self, results: List[Document]) -> List[ResearchTarget]:
        """Deduplicate results and prepare for scraping."""
        unique_results = {}
        
        for result in results:
            # Generate content hash
            content_hash = hashlib.md5(
                f"{result.page_content}{result.metadata['title']}".encode()
            ).hexdigest()
            
            url = result.metadata['link']
            domain = urlparse(url).netloc
            
            # Create research target
            target = ResearchTarget(
                url=url,
                source_type=self._determine_source_type(url),
                confidence_score=self._calculate_research_confidence(result),
                needs_scraping=self._needs_scraping(domain),
                content_hash=content_hash,
                last_checked=datetime.now().isoformat()
            )
            
            # Only keep highest confidence version of duplicate content
            if content_hash not in unique_results or \
               target.confidence_score > unique_results[content_hash].confidence_score:
                unique_results[content_hash] = target
        
        return list(unique_results.values())

    def _needs_scraping(self, domain: str) -> bool:
        """Determine if content needs ScrapingBee scraping."""
        no_scrape_needed = {
            'twitter.com', 'linkedin.com', 'facebook.com',  # API access needed
            'gov.uk', 'parliament.uk'  # Public data
        }
        return domain not in no_scrape_needed

    def _calculate_research_confidence(self, result: Document) -> float:
        """Calculate confidence score for research relevance."""
        score = 1.0
        content = f"{result.metadata['title']} {result.page_content}".lower()
        
        # Check for high-priority keywords
        for category, data in self.research_categories.items():
            if data["priority"] == "high":
                for keyword in data["keywords"]:
                    if keyword in content:
                        score *= 1.5
                        break

        # Source credibility
        if "gov.uk" in result.metadata['link']:
            score *= 2.0
        elif any(news in result.metadata['link'] for news in ['.bbc.', '.guardian.', '.independent.']):
            score *= 1.5

        # Recency
        if "2024" in content or "2023" in content:
            score *= 1.3

        return round(score, 2)

    def prepare_scraping_tasks(self, targets: List[ResearchTarget]) -> List[Dict]:
        """Prepare tasks for ScrapingBee."""
        scraping_tasks = []
        
        for target in targets:
            if target.needs_scraping:
                scraping_tasks.append({
                    "url": target.url,
                    "content_hash": target.content_hash,
                    "source_type": target.source_type,
                    "scraping_config": {
                        "wait_for": ".article-content, .main-content",
                        "block_resources": True,
                        "premium_proxy": True,
                        "country_code": "gb"
                    }
                })
        
        return scraping_tasks

    def save_research_results(self, councillor: Councillor, 
                            results: List[ResearchTarget], 
                            output_file: str = "research_results.json"):
        """Save structured research results."""
        research_data = {
            "councillor_name": f"{councillor.first_name} {councillor.last_name}",
            "council": councillor.council,
            "last_updated": datetime.now().isoformat(),
            "results": [
                {
                    "url": target.url,
                    "source_type": target.source_type,
                    "confidence_score": target.confidence_score,
                    "content_hash": target.content_hash,
                    "needs_scraping": target.needs_scraping,
                    "last_checked": target.last_checked
                }
                for target in results
            ]
        }

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(research_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Research results saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving research results: {e}")

def main():
    # Initialize the searcher
    searcher = CouncillorSearcher()
    
    # Search for all councillors
    results = searcher.search_all_councillors()
    
    # Save results to file
    searcher.save_results(results)
    
    # Process and display results
    for councillor_name, data in results.items():
        print(f"\nResults for {councillor_name}:")
        print("\nSummary:")
        for key, value in data["summary"].items():
            print(f"- {key}: {value}")
        
        print("\nDetailed Findings:")
        for category, documents in data.items():
            if category != "summary":
                print(f"\n{category.upper()}:")
                for doc in documents:
                    print(f"- Title: {doc.metadata['title']}")
                    print(f"  Link: {doc.metadata['link']}")
                    print(f"  Snippet: {doc.page_content[:200]}...")
                    print()

if __name__ == "__main__":
    main() 