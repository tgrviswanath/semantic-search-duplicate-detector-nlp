import React, { useState, useEffect } from "react";
import {
  Box, TextField, Button, CircularProgress, Alert, Typography,
  Paper, Chip, Divider, LinearProgress, IconButton, Tooltip,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import { searchDocs, addDocuments, getStats, clearIndex } from "../services/searchApi";

const SAMPLE_DOCS = [
  { text: "Apple Inc. reported record revenue of $119.6 billion in Q1 2024." },
  { text: "Microsoft acquired Activision Blizzard for $68.7 billion." },
  { text: "The Federal Reserve raised interest rates by 25 basis points." },
  { text: "Tesla reported a decline in vehicle deliveries for Q1 2024." },
  { text: "Amazon Web Services revenue grew 17% year-over-year in Q4 2023." },
  { text: "Google parent Alphabet posted strong ad revenue growth in 2024." },
  { text: "NVIDIA's data center revenue surged due to AI chip demand." },
  { text: "Meta Platforms reported a 25% increase in advertising revenue." },
  { text: "JPMorgan Chase reported record profits driven by higher interest rates." },
  { text: "The S&P 500 index reached an all-time high in early 2024." },
];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [rerank, setRerank] = useState(true);
  const [results, setResults] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [error, setError] = useState("");

  const fetchStats = async () => {
    try {
      const res = await getStats();
      setStats(res.data);
    } catch (_) {}
  };

  useEffect(() => { fetchStats(); }, []);

  const handleAddSamples = async () => {
    setIndexing(true);
    setError("");
    try {
      await addDocuments(SAMPLE_DOCS);
      await fetchStats();
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to add documents.");
    } finally {
      setIndexing(false);
    }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    setResults([]);
    try {
      const res = await searchDocs(query, topK, rerank);
      setResults(res.data.results);
    } catch (e) {
      setError(e.response?.data?.detail || "Search failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleClear = async () => {
    await clearIndex();
    setResults([]);
    setStats(null);
    await fetchStats();
  };

  const scoreColor = (s) => s > 5 ? "success" : s > 0 ? "warning" : "error";

  return (
    <Box>
      {/* Stats bar */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2, flexWrap: "wrap" }}>
        <Chip label={`📚 ${stats?.total_documents ?? 0} documents indexed`}
          color={stats?.total_documents > 0 ? "primary" : "default"} />
        <Chip label={`🤖 ${stats?.embed_model ?? "—"}`} variant="outlined" size="small" />
        <Button size="small" variant="outlined" onClick={handleAddSamples} disabled={indexing}
          startIcon={indexing ? <CircularProgress size={14} /> : null}>
          {indexing ? "Indexing..." : "Load 10 Sample Docs"}
        </Button>
        <Tooltip title="Clear index">
          <IconButton size="small" onClick={handleClear} color="error">
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      <Divider sx={{ mb: 2 }} />

      {/* Search bar */}
      <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
        <TextField
          fullWidth
          label="Search query"
          placeholder="e.g. AI chip demand revenue growth"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          size="small"
        />
        <TextField
          label="Top K"
          type="number"
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
          size="small"
          sx={{ width: 90 }}
          inputProps={{ min: 1, max: 20 }}
        />
        <Button variant="contained" onClick={handleSearch}
          disabled={!query.trim() || loading || !stats?.total_documents}
          startIcon={loading ? <CircularProgress size={16} color="inherit" /> : null}
          sx={{ whiteSpace: "nowrap" }}>
          {loading ? "Searching..." : "Search"}
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Results */}
      {results.length > 0 && (
        <Box>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            {results.length} results for "{query}"
          </Typography>
          {results.map((r, i) => (
            <Paper key={i} variant="outlined" sx={{ p: 2, mb: 1.5 }}>
              <Box sx={{ display: "flex", justifyContent: "space-between", mb: 1 }}>
                <Typography variant="body2" color="text.secondary">#{i + 1}</Typography>
                <Box sx={{ display: "flex", gap: 1 }}>
                  <Chip label={`Score: ${r.score.toFixed(3)}`}
                    color={scoreColor(r.score)} size="small" />
                  {r.bi_score !== r.score && (
                    <Chip label={`Bi: ${r.bi_score.toFixed(3)}`}
                      variant="outlined" size="small" />
                  )}
                </Box>
              </Box>
              <Typography variant="body1">{r.text}</Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min(Math.max((r.score + 10) * 5, 0), 100)}
                sx={{ mt: 1, height: 4, borderRadius: 2 }}
                color={scoreColor(r.score)}
              />
            </Paper>
          ))}
        </Box>
      )}

      {results.length === 0 && !loading && query && (
        <Alert severity="info">No results found. Try a different query or load sample documents.</Alert>
      )}
    </Box>
  );
}
