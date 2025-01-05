import { useState } from "react";
import { Input } from "@/components/ui/input";
import { CouncillorCard } from "@/components/CouncillorCard";
import councillorData from "../data/councillor_results.json";
import { CouncillorResults } from "@/types/councillor";

const Index = () => {
  const [searchTerm, setSearchTerm] = useState("");
  
  const filteredCouncillors = Object.entries(councillorData as CouncillorResults)
    .filter(([name]) => 
      name.toLowerCase().includes(searchTerm.toLowerCase())
    );

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8 text-primary">Councillor Web Results</h1>
      
      <Input
        type="search"
        placeholder="Search councillors..."
        className="mb-8"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCouncillors.map(([name, data]) => (
          <CouncillorCard key={name} name={name} data={data} />
        ))}
      </div>
      
      {filteredCouncillors.length === 0 && (
        <p className="text-center text-gray-500 mt-8">
          No councillors found matching your search.
        </p>
      )}
    </div>
  );
};

export default Index;