import React from 'react';
import { Box, Typography } from '@mui/material';
import { useAllContext } from '../components/Context';

const Settings = () => {
  const { roles } = useAllContext();

  if (roles.includes("admin")) {
    return (
      <Box>
        <Typography>My Settings</Typography>
      </Box>
    )
  } else {
    return (
      <Box>
        <Typography>Access Restricted</Typography>
      </Box>
    )
  }
};

export default Settings;