import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Container, Box, Drawer, List, ListItem, ListItemText, CssBaseline } from '@mui/material';
import Dashboard from './components/Dashboard';
import Buildings from './components/Buildings';
import Companies from './components/Companies';

const drawerWidth = 240;

function App() {
  return (
    <BrowserRouter>
      <Box sx={{ display: 'flex' }}>
        <CssBaseline />
        <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
          <Toolbar>
            <Typography variant="h6" noWrap component="div">
              Капитальный ремонт - Управление
            </Typography>
          </Toolbar>
        </AppBar>
        
        <Drawer
          variant="permanent"
          sx={{
            width: drawerWidth,
            flexShrink: 0,
            '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box' },
          }}
        >
          <Toolbar />
          <Box sx={{ overflow: 'auto' }}>
            <List>
              <ListItem button component={Link} to="/">
                <ListItemText primary="Дашборд" />
              </ListItem>
              <ListItem button component={Link} to="/buildings">
                <ListItemText primary="Здания" />
              </ListItem>
              <ListItem button component={Link} to="/companies">
                <ListItemText primary="Управляющие компании" />
              </ListItem>
            </List>
          </Box>
        </Drawer>
        
        <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
          <Toolbar />
          <Container maxWidth="xl">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/buildings" element={<Buildings />} />
              <Route path="/companies" element={<Companies />} />
            </Routes>
          </Container>
        </Box>
      </Box>
    </BrowserRouter>
  );
}

export default App;
