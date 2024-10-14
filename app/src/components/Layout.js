import React from 'react';
import { Box, Toolbar, } from '@mui/material';
import { Outlet } from 'react-router-dom';
import NavBar from './NavBar';
import LoadingScreen from './LoadingScreen';
import { ContextProvider } from './Context';
import AlertSnackbar from './AlertSnackbar';

export default function Layout() {

  return (
    <ContextProvider>
      <Box sx={{ display: 'flex' }}>
        <NavBar />
        <Box component='main' height='100%' width='100%' sx={{ flexGrow: 1, p: 3, overflow: 'auto' }}>
          <Toolbar />
          <Outlet />
        </Box>
        <LoadingScreen />
        <AlertSnackbar />
      </Box>
    </ContextProvider>
  )
}