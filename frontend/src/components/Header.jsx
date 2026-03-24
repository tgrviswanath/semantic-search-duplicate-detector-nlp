import { AppBar, Toolbar, Typography } from "@mui/material";
import SearchIcon from "@mui/icons-material/Search";

export default function Header() {
  return (
    <AppBar position="static" color="primary">
      <Toolbar sx={{ gap: 1 }}>
        <SearchIcon />
        <Typography variant="h6" fontWeight="bold">
          Semantic Search & Duplicate Detector
        </Typography>
      </Toolbar>
    </AppBar>
  );
}
