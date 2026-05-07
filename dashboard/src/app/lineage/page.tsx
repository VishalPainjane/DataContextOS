"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Handle,
  Position,
  NodeProps,
  Node,
  Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { buildApiUrl } from "../../lib/api";
import { Card, CardContent } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Button } from "../../components/ui/button";
import { GitMerge, Search, LayoutTemplate } from "lucide-react";

interface LineageNodeData extends Record<string, unknown> {
  asset_id: string;
  asset_name: string;
  asset_type: string;
  domain: string;
  owner: string;
  depth: number;
  isRoot?: boolean;
}

interface LineageEdge {
  source_id: string;
  target_id: string;
  edge_type: string;
  transformation?: string;
}

interface LineageResponse {
  root_asset_id: string;
  nodes: LineageNodeData[];
  edges: LineageEdge[];
}

type CustomNodeType = Node<LineageNodeData, 'custom'>;

const CustomNode = ({ data }: NodeProps<CustomNodeType>) => {
  const isRoot = data.isRoot;
  
  return (
    <div className={`p-4 rounded-xl backdrop-blur-xl border w-[240px] shadow-lg ${isRoot ? 'bg-primary/10 border-primary/50 shadow-primary/20' : 'bg-card/70 border-border/50'}`}>
      <Handle type="target" position={Position.Top} className="w-3 h-3 bg-muted-foreground border-2 border-background" />
      <div className="text-[10px] font-semibold text-muted-foreground mb-1.5 uppercase tracking-wider flex items-center gap-1.5">
        <LayoutTemplate className="w-3 h-3" /> {data.asset_type}
      </div>
      <div className="font-bold text-[15px] mb-3 leading-tight line-clamp-2">
        {data.asset_name}
      </div>
      <div className="flex justify-between text-xs text-muted-foreground/80 font-medium">
        <span className="truncate pr-2">{data.domain || 'General'}</span>
        <span className="truncate">{data.owner || 'Unassigned'}</span>
      </div>
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-primary border-2 border-background" />
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

function LineageContent() {
  const searchParams = useSearchParams();
  const initialAssetId = searchParams?.get("asset");
  
  const [assetId, setAssetId] = useState(initialAssetId || "");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [nodes, setNodes, onNodesChange] = useNodesState<CustomNodeType>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const fetchLineage = async (id: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(buildApiUrl(`/api/lineage/${id}?depth=2`));
      if (!res.ok) throw new Error("Failed to fetch lineage data");
      
      const data: LineageResponse = await res.json();
      
      // Auto-layout logic (simple layered layout)
      const newNodes = data.nodes.map((node) => {
        let y = 0;
        let x = Math.random() * 400 - 200; 
        
        if (node.asset_id === data.root_asset_id) {
            x = 0;
            y = 200;
        } else {
            const isUpstream = data.edges.some(e => e.source_id === node.asset_id);
            if (isUpstream) {
                y = 50;
            } else {
                y = 350;
            }
        }

        return {
          id: node.asset_id,
          type: 'custom' as const,
          position: { x, y },
          data: {
            ...node,
            isRoot: node.asset_id === data.root_asset_id
          }
        };
      });

      const newEdges = data.edges.map(edge => ({
        id: `${edge.source_id}-${edge.target_id}`,
        source: edge.source_id,
        target: edge.target_id,
        animated: true,
        style: { stroke: 'hsl(var(--primary))', strokeWidth: 2, opacity: 0.6 },
        label: edge.transformation || undefined,
        labelStyle: { fill: 'hsl(var(--foreground))', fontSize: 12, fontWeight: 500 },
        labelBgStyle: { fill: 'hsl(var(--background))', fillOpacity: 0.8, stroke: 'hsl(var(--border))', strokeWidth: 1 },
      }));

      setNodes(newNodes);
      setEdges(newEdges);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (initialAssetId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      fetchLineage(initialAssetId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialAssetId]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (assetId) fetchLineage(assetId);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)] gap-6 animate-in fade-in duration-500">
      
      <div className="space-y-2">
        <h1 className="text-4xl font-extrabold tracking-tight flex items-center gap-3">
          <GitMerge className="w-9 h-9 text-primary" />
          Lineage Explorer
        </h1>
        <p className="text-xl text-muted-foreground">Visualize upstream dependencies and downstream impacts.</p>
      </div>

      <Card className="bg-card/50 backdrop-blur-sm border-border/50">
        <CardContent className="p-4">
          <form onSubmit={handleSearch} className="flex gap-3 items-center">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input 
                type="text" 
                placeholder="Enter Asset ID..." 
                value={assetId}
                onChange={(e) => setAssetId(e.target.value)}
                className="pl-9 h-11 bg-background/50"
              />
            </div>
            <Button type="submit" className="h-11 px-8" disabled={isLoading || !assetId}>
              {isLoading ? 'Loading...' : 'Explore'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {error && (
        <div className="p-4 bg-destructive/10 text-destructive border border-destructive/20 rounded-xl">
          Error: {error}
        </div>
      )}

      <div className="flex-1 rounded-xl border border-border/50 bg-background/30 backdrop-blur-sm overflow-hidden relative shadow-inner">
        {nodes.length === 0 && !isLoading && !error ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-muted-foreground">
            <GitMerge className="w-16 h-16 mb-4 text-muted-foreground/30" />
            <div className="text-lg font-medium">Enter an Asset ID to view its lineage graph.</div>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            minZoom={0.2}
            className="bg-transparent"
          >
            <Background color="hsl(var(--muted-foreground))" gap={16} size={1} />
            <Controls className="bg-card border-border shadow-md" />
            <MiniMap className="bg-card border-border shadow-md" maskColor="hsl(var(--background) / 0.8)" />
          </ReactFlow>
        )}
      </div>

    </div>
  );
}

export default function LineageExplorer() {
  return (
    <Suspense fallback={<div className="p-10 text-muted-foreground">Loading explorer...</div>}>
      <LineageContent />
    </Suspense>
  );
}

