import { useState } from "react"
import { createFileRoute } from "@tanstack/react-router"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { ScreenplaysService } from "@/client"
import { Button } from "@/components/ui/button"

export const Route = createFileRoute("/_layout/screenplays")({
  component: Screenplays,
})

function Screenplays() {
  const queryClient = useQueryClient()
  const [file, setFile] = useState<File | null>(null)
  const [selectedReport, setSelectedReport] = useState<any>(null)

  const { data, isLoading } = useQuery({
    queryKey: ["screenplays"],
    queryFn: () => ScreenplaysService.readScreenplays({}),
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
  ScreenplaysService.uploadScreenplay({
    formData: { file: file as unknown as string },
  }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["screenplays"] })
      setFile(null)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => ScreenplaysService.deleteScreenplay({ id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["screenplays"] })
    },
  })

  const handleUpload = () => {
    if (file) uploadMutation.mutate(file)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Script Coverage AI</h1>

      <div className="border rounded-lg p-4 mb-8 flex items-center gap-4">
        <input
          type="file"
          accept=".txt,.pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <Button onClick={handleUpload} disabled={!file || uploadMutation.isPending}>
          {uploadMutation.isPending ? "Analyzing..." : "Upload & Analyze"}
        </Button>
      </div>

      {isLoading ? (
        <p>Loading screenplays...</p>
      ) : (
        <div className="space-y-3">
          {data?.data.map((sp: any) => (
            <div
              key={sp.id}
              className="border rounded-lg p-4 flex justify-between items-center"
            >
              <div>
                <p className="font-semibold">{sp.title}</p>
                <p className="text-sm text-muted-foreground">
                  Status: {sp.status}
                </p>
              </div>
              <div className="flex gap-2">
                {sp.status === "completed" && (
                  <Button variant="outline" onClick={() => setSelectedReport(sp)}>
                    View Report
                  </Button>
                )}
                <Button
                  variant="destructive"
                  onClick={() => deleteMutation.mutate(sp.id)}
                >
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selectedReport && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center p-4"
          onClick={() => setSelectedReport(null)}
        >
          <div
            className="bg-background rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-xl font-bold mb-4">{selectedReport.title}</h2>
            <pre className="whitespace-pre-wrap text-sm">
              {JSON.stringify(selectedReport.coverage_report, null, 2)}
            </pre>
            <Button className="mt-4" onClick={() => setSelectedReport(null)}>
              Close
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}