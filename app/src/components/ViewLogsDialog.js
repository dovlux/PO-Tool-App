import React, { useState, useMemo } from "react";
import {
  Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack
} from '@mui/material';
import LogoDevIcon from '@mui/icons-material/LogoDev';
import DataTable from "./DataTable";

export default function ViewLogsDialog({ row }) {
  const [open, setOpen] = useState(false);

  const logColumns = useMemo(() => [
    { field: 'user', headerName: 'User', width: 80 },
    { field: 'message', headerName: 'Message', width: 200 },
    { field: 'type', headerName: 'Type', width: 75 },
    { field: 'date', type: 'datetime', headerName: 'Date', width: 250,
      valueGetter: (value) => new Date(value),
    },
  ], []);

  const logRows = useMemo(() => row.logs.map((log, index) => ({
    id: index, ...log,
  })), [row.logs]);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <Stack direction='row' alignContent='center' spacing={1} m={1}>
      <Button onClick={handleOpen} >
        <LogoDevIcon color="secondary" />
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        fullWidth
      >
        <DialogTitle>{`Logs for ${row.name}`}</DialogTitle>
        <DialogContent>
          <DataTable
            rows={logRows}
            columns={logColumns}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Close</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}