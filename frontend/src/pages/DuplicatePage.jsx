import React, { useState } from "react";
import {
  Box, TextField, Button, CircularProgress, Alert, Typography,
  Paper, Chip, Slider, Divider,
} from "@mui/material";
import { findDuplicates } from "../services/searchApi";

const PLACEHOLDER = `How do I reset my password?
I forgot my password, how can I recover it?
What are your business hours?
When is your office open?
I want to cancel my subscription.
How do I unsubscribe from the service?
The app is not working on my phone.
My mobile application keeps crashing.`;

export default function DuplicatePage() {
  const [input, setInput] = useState("");
  const [threshold, setThreshold] = useState(0.75);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDetect = async () => {
    const texts = input.split("\n").map((t) => t.trim()).filter(Boolean);
    if (texts.length < 2) {
      setError("Enter at least 2 texts.");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await findDuplicates(texts, threshold);
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || "Duplicate detection failed.");
    } finally {
      setLoading(false);
    }
  };

  const simColor = (s) => s >= 0.9 ? "error" : s >= 0.8 ? "warning" : "info";

  return (
    <Box>
      <Typography variant="h6" gutterBottom>Duplicate / Near-Duplicate Detector</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Enter one text per line. The system finds semantically similar pairs above the threshold.
      </Typography>

      <Button size="small" variant="text" onClick={() => setInput(PLACEHOLDER)} sx={{ mb: 1 }}>
        Load sample texts
      </Button>

      <TextField
        fullWidth multiline rows={8}
        label="Enter texts (one per line)"
        placeholder={PLACEHOLDER}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        sx={{ mb: 2 }}
      />

      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" gutterBottom>
          Similarity threshold: <strong>{threshold}</strong>
        </Typography>
        <Slider value={threshold} min={0.5} max={1.0} step={0.05}
          onChange={(_, v) => setThreshold(v)}
          marks={[{ value: 0.5, label: "0.5" }, { value: 0.75, label: "0.75" }, { value: 1.0, label: "1.0" }]}
        />
      </Box>

      <Button variant="contained" fullWidth size="large"
        disabled={!input.trim() || loading} onClick={handleDetect}
        startIcon={loading ? <CircularProgress size={18} color="inherit" /> : null}
      >
        {loading ? "Detecting..." : "Find Duplicates"}
      </Button>

      {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}

      {result && (
        <Box sx={{ mt: 3 }}>
          <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
            <Chip
              label={result.count > 0 ? `⚠️ ${result.count} duplicate pair(s) found` : "✅ No duplicates found"}
              color={result.count > 0 ? "warning" : "success"}
            />
            <Chip label={`Threshold: ${result.threshold}`} variant="outlined" size="small" />
          </Box>

          {result.pairs.map((pair, i) => (
            <Paper key={i} variant="outlined" sx={{ p: 2, mb: 1.5, borderColor: simColor(pair.similarity) + ".main" }}>
              <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 1 }}>
                <Chip
                  label={`Similarity: ${(pair.similarity * 100).toFixed(1)}%`}
                  color={simColor(pair.similarity)}
                  size="small"
                />
              </Box>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>A:</strong> {pair.text_a}
              </Typography>
              <Divider sx={{ my: 1 }} />
              <Typography variant="body2">
                <strong>B:</strong> {pair.text_b}
              </Typography>
            </Paper>
          ))}
        </Box>
      )}
    </Box>
  );
}
