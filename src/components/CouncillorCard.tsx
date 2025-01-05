import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Briefcase, Info, Share2 } from "lucide-react";
import { CouncillorData } from "@/types/councillor";
import { useNavigate } from "react-router-dom";

interface CouncillorCardProps {
  name: string;
  data: CouncillorData;
}

export const CouncillorCard = ({ name, data }: CouncillorCardProps) => {
  const navigate = useNavigate();
  const { summary } = data;

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "basic_info":
        return <Info className="h-4 w-4" />;
      case "business_interests":
        return <Briefcase className="h-4 w-4" />;
      case "social_media":
        return <Share2 className="h-4 w-4" />;
      case "controversy":
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return null;
    }
  };

  return (
    <Card 
      className="hover:shadow-lg transition-shadow cursor-pointer"
      onClick={() => navigate(`/councillor/${encodeURIComponent(name)}`)}
    >
      <CardHeader>
        <CardTitle className="text-xl font-semibold">{name}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex gap-2 flex-wrap">
            {Object.entries(data.categories).map(([category, results]) => 
              results.length > 0 && (
                <Badge 
                  key={category}
                  variant="secondary"
                  className="flex items-center gap-1"
                >
                  {getCategoryIcon(category)}
                  {category.replace('_', ' ')} ({results.length})
                </Badge>
              )
            )}
          </div>
          <div className="text-sm text-gray-600">
            <p>Total Results: {summary.total_results}</p>
            {summary.controversy_count > 0 && (
              <p className="text-red-500 flex items-center gap-1">
                <AlertTriangle className="h-4 w-4" />
                Controversy Items: {summary.controversy_count}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};