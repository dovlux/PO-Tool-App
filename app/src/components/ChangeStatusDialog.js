import React, { Fragment, useState } from "react";
import {
  Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle,
  CircularProgress, Select,
  MenuItem,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import sendRequest from '../utils/sendRequest'

export default function ChangeStatusDialog({ row, addSnackbar, fetchPos }) {
  const [open, setOpen] = useState(false);
  const [loadingChange, setLoadingChange] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('');

  const handleOpen = () => {
    setSelectedStatus('');
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
      addSnackbar(error.message, false);
    } finally {
      setLoadingChange(false);
      handleClose();
    }
  }

  return (
    <Fragment>
      <Button onClick={handleOpen} >
        <EditIcon color="secondary" />
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
            {(!row.is_ats) && (<MenuItem value="Breakdown Created">Breakdown Created</MenuItem>)}
            {(!row.is_ats) && (<MenuItem value="Net Sales Calculated">Net Sales Calculated</MenuItem>)}
            {(!row.is_ats) && (<MenuItem value="PO Created">PO Created</MenuItem>)}
            <MenuItem value="PO Received">PO Received</MenuItem>
            <MenuItem value="Internal Error">Internal Error</MenuItem>
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