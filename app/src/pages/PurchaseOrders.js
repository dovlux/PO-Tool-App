import React from 'react';
import { Stack, Typography, Box, IconButton } from '@mui/material';
import DataTable from '../components/DataTable';
import CreatePoDialog from '../components/CreatePoDialog';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useAllContext } from '../components/Context';

const PoHeader = ({ roles, fetchPos }) => {
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
        {(roles.includes("buyer") || roles.includes("admin")) && (
          <CreatePoDialog />
        )}
        <IconButton
          color="inherit"
          aria-label="refresh table"
          onClick={fetchPos(false)}
        >
          <RefreshIcon />
        </IconButton>
      </Stack>
    </Stack>
  )
}

const PurchaseOrders = () => {
  const { roles, poRows, poColumns, fetchPos } = useAllContext();

  return (
    <Box>
      <PoHeader roles={roles} fetchPos={fetchPos} />
      <DataTable rows={poRows} columns={poColumns} />
    </Box>
  )
};

export default PurchaseOrders;