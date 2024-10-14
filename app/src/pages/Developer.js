import React from 'react';
import { Box, Typography, Stack, IconButton, } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useAllContext } from '../components/Context';
import DataTable from '../components/DataTable';

const DevHeader = ({ fetchCacheStatus }) => {
  return (
    <Stack
      direction='row'
      sx={{
        padding: 2,
        display: 'flex',
        width: '100%',
        alignItems: 'center',
        justifyContent: 'space-between',
        pt: 1.5,
      }}
      spacing={1}
    >
      <Typography variant='h4'>
        Dependent Spreadsheets
      </Typography>
      <IconButton
        color="inherit"
        aria-label="refresh table"
        onClick={() => fetchCacheStatus(false)}
      >
        <RefreshIcon />
      </IconButton>
    </Stack>
  )
}

const Developer = () => {
  const { roles, cacheRows, cacheColumns, fetchCacheStatus } = useAllContext();

  if (roles.includes("developer")) {
    return (
      <Box width='50%' height='25%' border={1} sx={{ overflow: 'hidden', overflowY: 'auto' }}>
        <DevHeader fetchCacheStatus={fetchCacheStatus} />
        <DataTable rows={cacheRows} columns={cacheColumns} />
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

export default Developer;