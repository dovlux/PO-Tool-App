import React, { Fragment, useState } from "react";
import {
  Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle,
  CircularProgress, Select,
  MenuItem,
} from '@mui/material';
import sendRequest from '../utils/sendRequest'

export default function ChangeStatusDialog({ row, addSnackbar, fetchPos }) {
  const [open, setOpen] = useState(false);
  const [loadingChange, setLoadingChange] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('');

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    if (!loadingChange) {
      setOpen(false);
    }
  };

  const changeStatus = async (id, status) => {
    setLoadingChange(true);
    try {
      let response = await sendRequest(
        `purchase-orders/${id}`, { status: status, spreadsheet_id: null }, 'PUT'
      );
      fetchPos();
      addSnackbar(response.message);
    } catch (error) {
      addSnackbar(error.message, true);
    } finally {
      setLoadingChange(false);
      handleClose();
    }
  }

  return (
    <Fragment>
      <Button
        variant="contained"
        color="secondary"
        onClick={handleOpen}
      >
        Change Status
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        disableEscapeKeyDown={loadingChange}
      >
        <DialogTitle>Change Purchase Order Status</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Please select the status to be applied.
          </DialogContentText>
          <Select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            fullWidth
            disabled={loadingChange}
          >
            <MenuItem value="">Select Status</MenuItem>
            <MenuItem value="Worksheet Created">Worksheet Created</MenuItem>
            <MenuItem value="Breakdown Created">Breakdown Created</MenuItem>
          </Select>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loadingChange}>Cancel</Button>
          <Button onClick={() => changeStatus(row.id, selectedStatus)}
            disabled={loadingChange || !selectedStatus}
          >
            {loadingChange ? <CircularProgress size={24} /> : 'Change Status'}
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  )
}