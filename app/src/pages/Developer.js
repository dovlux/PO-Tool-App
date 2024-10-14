import React, { useEffect, useState, useCallback } from 'react';
import { Box, Typography, Stack, IconButton, } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import DataTable from '../components/DataTable';
import sendRequest from '../utils/sendRequest';
import UpdateCacheButton from "../components/UpdateCacheButton";

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

const Developer = ({ setLoading, addSnackbar }) => {
  const [cacheRows, setCacheRows] = useState([]);
  const cacheColumns = [
    { field: 'name', headerName: 'Sheet Name', width: 200 },
    { field: 'status', headerName: 'Status', width: 150 },
    {
      field: 'update_time',
      headerName: 'Last Updated',
      width: 200,
      valueGetter: (value) => new Date(value).toLocaleString(),
    },
    {
      field: 'update',
      headerName: 'Update',
      width: 200,
      sortable: false,
      headerAlign: 'center',
      renderCell: (params) => (
        <UpdateCacheButton
          row={params.row}
          fetchCacheStatus={fetchCacheStatus}
          addSnackbar={addSnackbar}
        />
      )
    }
  ];

  const getCacheStatus = async () => {
    let data = await sendRequest('dev/cache/status');
    let rows = data.map((row, index) => ({ ...row, id: index }));
    return rows;
  };

  const fetchCacheStatus = useCallback(async (background = false) => {
    if (!background) setLoading(true);
    try {
      let rows = await getCacheStatus();
      setCacheRows(rows);
    } catch (error) {
      if (!background) addSnackbar(error.message);
    } finally {
      if (!background) setLoading(false);
    }
  }, [addSnackbar, setLoading]);

  useEffect(() => {
    fetchCacheStatus();
    const intervalId = setInterval(() => fetchCacheStatus(true), 15000);
    return () => clearInterval(intervalId);
  }, [fetchCacheStatus]);

  return (
    <Box width='50%' height='25%' border={1} sx={{ overflow: 'hidden', overflowY: 'auto' }}>
      <DevHeader fetchCacheStatus={fetchCacheStatus} />
      <DataTable rows={cacheRows} columns={cacheColumns} />
    </Box>
  )
}

export default Developer;