import { useParams } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { AlertTriangle, ArrowLeft, Briefcase, ExternalLink, Info, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { CouncillorResults, SearchResult } from "@/types/councillor";
import councillorData from "../data/councillor_results.json";

const ResultCard = ({ result }: { result: SearchResult }) => (
  <Card className="mb-4">
    <CardContent className="pt-4">
      <a 
        href={result.link} 
        target="_blank" 
        rel="noopener noreferrer"
        className="text-primary hover:underline flex items-center gap-2"
      >
        {result.title}
        <ExternalLink className="h-4 w-4" />
      </a>
      <p className="text-sm text-gray-600 mt-2">{result.snippet}</p>
      <div className="flex justify-between items-center mt-2 text-sm text-gray-500">
        <span>Relevance: {result.relevance_score.toFixed(1)}</span>
        {result.search_time && <span>{result.search_time}</span>}
      </div>
    </CardContent>
  </Card>
);

export const CouncillorDetail = () => {
  const { name } = useParams();
  const navigate = useNavigate();
  
  if (!name) return null;
  
  const decodedName = decodeURIComponent(name);
  const councillor = (councillorData as CouncillorResults)[decodedName];
  
  if (!councillor) {
    return <div>Councillor not found</div>;
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "business_interests":
        return <Briefcase className="h-4 w-4" />;
      case "controversy":
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const filteredCategories = Object.entries(councillor.categories).filter(
    ([category]) => !['basic_info', 'social_media'].includes(category)
  );

  return (
    <div className="container mx-auto py-8 px-4">
      <Button 
        variant="outline" 
        onClick={() => navigate('/')}
        className="mb-6"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to List
      </Button>
      
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="text-2xl">{decodedName}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold">Total Results</h3>
              <p className="text-2xl">{councillor.summary.total_results}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold">Controversy Count</h3>
              <p className="text-2xl text-red-500">{councillor.summary.controversy_count}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-semibold">Potential Interests</h3>
              <p className="text-2xl">{councillor.summary.potential_interests.length}</p>
            </div>
          </div>
        </CardContent>
      </Card>
      

      <Accordion type="single" collapsible className="space-y-4">
        {filteredCategories.map(([category, results]) => (
          <AccordionItem value={category} key={category}>
            <AccordionTrigger className="flex items-center gap-2">
              {getCategoryIcon(category)}
              {category.replace('_', ' ')} ({results.length})
            </AccordionTrigger>
            <AccordionContent>
              {results.map((result, index) => (
                <ResultCard key={index} result={result} />
              ))}
              {results.length === 0 && (
                <p className="text-gray-500 italic">No results found</p>
              )}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
};