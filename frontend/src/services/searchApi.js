import axios from "axios";

const api = axios.create({ baseURL: process.env.REACT_APP_API_URL });

export const addDocuments  = (documents) => api.post("/api/v1/documents", { documents });
export const searchDocs    = (query, top_k, rerank) => api.post("/api/v1/search", { query, top_k, rerank });
export const findDuplicates = (texts, threshold) => api.post("/api/v1/duplicates", { texts, threshold });
export const getStats      = () => api.get("/api/v1/stats");
export const clearIndex    = () => api.delete("/api/v1/documents");
