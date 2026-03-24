import React, { useState } from "react";
import { Container, Box, Tabs, Tab } from "@mui/material";
import Header from "./components/Header";
import SearchPage from "./pages/SearchPage";
import DuplicatePage from "./pages/DuplicatePage";

export default function App() {
  const [tab, setTab] = useState(0);
  return (
    <>
      <Header />
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 3 }}>
          <Tab label="Semantic Search" />
          <Tab label="Duplicate Detector" />
        </Tabs>
        <Box>{tab === 0 ? <SearchPage /> : <DuplicatePage />}</Box>
      </Container>
    </>
  );
}
