# Councillor Insights Hub 🔍

An automated OSINT tool for gathering and analyzing background information on Reform UK councillors and candidates. The system helps researchers efficiently discover relevant information about political figures, including their business interests, controversies, and social media presence.

## 🎯 Purpose

This tool assists time-constrained researchers by:
- Automating the discovery of public information about councillors
- Identifying potential areas of interest or concern
- Aggregating data from multiple sources into a searchable format
- Highlighting opportunities for further manual investigation

## 🛠 Technical Stack

- **Frontend**: React + TypeScript with ShadcnUI
- **Backend**: Python
  - LangChain for structured data processing
  - Google Custom Search API for intelligent web searches
  - Data caching and rate limiting
- **Deployment**: Vercel
- **Data Storage**: JSON + SQLite

## 🔑 Key Features

- **Automated Search Pipeline**
  - Multi-stage search process
  - Intelligent filtering of baseline results
  - Category-based result organization
  - Confidence scoring for matches

- **Information Categories**
  - Business interests and directorships
  - Controversies and complaints
  - Social media presence
  - Voting records
  - Party affiliations and changes

- **Research Tools**
  - Relevance scoring
  - Source validation
  - Duplicate detection
  - Data persistence

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- Google Custom Search API credentials
- ScrapingBee API key (optional)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Blue-Cardigan/councillor-insights-hub.git
cd councillor-insights-hub
```

2. Install dependencies:
```bash
Backend
pip install -r requirements.txt

Frontend
npm install



## 📊 Data Sources

- Google Custom Search

## 📝 Notes for Researchers

### Automated vs Manual Research
- **Automated**
  - Initial data gathering
  - Social media discovery
  - News article collection
  - Business interest identification

- **Manual Review Required**
  - Verification of findings
  - Context analysis
  - Pattern identification
  - Source credibility assessment

### Research Opportunities
- Cross-reference with local planning decisions
- Monitor social media engagement patterns
- Track voting consistency
- Analyze business network connections

## 📄 License

This project is licensed under the MIT License.

## 👥 Team

- **Project Lead**: Jethro Reeve
- **Development**: Heidi Swigon

## 🔗 Links

- [Live Demo](https://councillor-insights-hub.vercel.app)