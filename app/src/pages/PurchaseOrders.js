import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Stack, Typography, Box, IconButton } from '@mui/material';
import DataTable from '../components/DataTable';
import CreatePoDialog from '../components/CreatePoDialog';
import RefreshIcon from '@mui/icons-material/Refresh';
import sendRequest from '../utils/sendRequest';
import { ReactComponent as GoogleSheetsIcon } from '../icons/google-sheets-icon.svg';
import { ReactComponent as SellerCloudIcon } from '../icons/sellercloud-icon.svg';
import ActionRowButtons from "../components/ActionRowButtons";
import DevRowButtons from '../components/DevRowButtons';

const PoHeader = ({ fetchPos, addSnackbar }) => {
  return (
    <Stack
      direction='row'
      sx={{
        display: 'flex',
        width: '100%',
        alignItems: 'center',
        justifyContent: 'space-between',
        pt: 1.5,
      }}
      spacing={2}
    >
      <Typography variant='h4'>
        Purchase Orders
      </Typography>
      <Stack direction='row' sx={{ gap: 1 }}>
        <CreatePoDialog addSnackbar={addSnackbar} fetchPos={fetchPos} />
        <IconButton
          color="inherit"
          aria-label="refresh table"
          onClick={() => fetchPos(false)}
        >
          <RefreshIcon />
        </IconButton>
      </Stack>
    </Stack>
  )
}

const PurchaseOrders = ({ addSnackbar, setLoading }) => {
  const [poRows, setPoRows] = useState([]);

  const fetchPos = useCallback(async (background = false) => {
    if (!background) setLoading(true);
    try {
      let poRows = await getPurchaseOrders();
      setPoRows(poRows);
    } catch (error) {
      if (!background) addSnackbar(error.message);
    } finally {
      if (!background) setLoading(false);
    }
  }, [addSnackbar, setLoading]);

  const poColumns = useMemo(() => [
    { field: 'id', type: 'number', headerName: 'ID', width: 70, sortable: true },
    { field: 'is_ats', headerName: 'Type', width: 70, valueGetter: (value) => value ? "ATS" : "LUX" },
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'date_created', type: 'date', headerName: 'Date Created', width: 150,
      valueGetter: (value) => new Date(JSON.parse(value)),
    },
    { field: 'status', headerName: 'Status', width: 300 },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 150,
      sortable: false,
      headerAlign: 'center',
      renderCell: (params) => <ActionRowButtons
        row={params.row} addSnackbar={addSnackbar} fetchPos={fetchPos}
      />
    },
    { field: 'spreadsheet_id', headerName: 'GS', headerAlign: 'center', width: 50, sortable: false, renderCell: (params) => {
        if (!params.value) {
          return null;
        }
        return (
          <IconButton
            component="a"
            href={'https://docs.google.com/spreadsheets/d/' + params.value}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="open google sheet"
          >
            <GoogleSheetsIcon style={{ height: '24px', width: '24px' }} />
          </IconButton>
        );
      }
    },
    { field: 'po_id', headerName: 'SC', headerAlign: 'center', width: 50, sortable: false, renderCell: (params) => {
        if (!params.value) {
          return null;
        }
        return (
          <IconButton
            component="a"
            href={'https://lux.delta.sellercloud.com/purchasing/po-details.aspx?id=' + params.value}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="open purchase order"
          >
            <SellerCloudIcon style={{ height: '24px', width: '24px' }} />
          </IconButton>
        );
      }
    },
    {
      field: 'dev',
      headerName: 'Dev Tools',
      width: 150,
      sortable: false,
      headerAlign: 'center',
      renderCell: (params) => <DevRowButtons
        row={params.row} addSnackbar={addSnackbar} fetchPos={fetchPos}
      />
    },
  ], [addSnackbar, fetchPos]);

  const getPurchaseOrders = async () => {
    let data = await sendRequest('purchase-orders');
    let rows = data;
    return rows
  };

  useEffect(() => {
    fetchPos();
    const intervalId = setInterval(() => fetchPos(true), 15000);
    return () => clearInterval(intervalId);
  }, [fetchPos]);

  return (
    <Box>
      <PoHeader fetchPos={fetchPos} addSnackbar={addSnackbar} />
      <DataTable rows={poRows} columns={poColumns} />
    </Box>
  )
};

export default PurchaseOrders;