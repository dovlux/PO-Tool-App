import React from 'react';
import { DataGrid } from '@mui/x-data-grid';
import Box from '@mui/material/Box'

export default function DataTable({ rows, columns }) {
  return (
    <Box sx={{
      height: '100%', width: '100%', display: 'flex',
      flexDirection: 'column', mt: 2,
    }}>
      <DataGrid
        rows={rows}
        columns={columns}
        initialState={{
          sorting: {
            sortModel: [{ field: 'id', sort: 'desc' }],
          },
          pagination: {
            paginationModel: { page: 0, pageSize: 50 },
          }
        }}
        pageSizeOptions={[50, 100]}
        disableRowSelectionOnClick
        sx={{ height: '100%', width: '100%', }}
      />
    </Box>
  );
}