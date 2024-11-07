import React, { Fragment, useState } from "react";
import {
  Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle,
  CircularProgress,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import sendRequest from '../utils/sendRequest'

export default function CreateBreakdownDialog({ buttonLoading, setButtonLoading, id, addSnackbar, fetchPos }) {
  const [open, setOpen] = useState(false);
  const [loadingBreakdown, setLoadingBreakdown] = useState(false);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    if (!loadingBreakdown) {
      setOpen(false);
    }
  };

  const createBreakdown = async (id) => {
    handleClose();
    setButtonLoading(true);
    setLoadingBreakdown(true);
    try {
      let response = await sendRequest(`purchase-orders/${id}/create-breakdown`);
      fetchPos();
      addSnackbar(response.message);
    } catch (error) {
      addSnackbar(error.message, false);
    } finally {
      setButtonLoading(false);
      setLoadingBreakdown(false);
    }
  }

  return (
    <Fragment>
      <Button
        disabled={buttonLoading}
        onClick={handleOpen}
      >
        {loadingBreakdown ? <CircularProgress size={24} /> : <PlayArrowIcon color="success" />}
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        disableEscapeKeyDown={loadingBreakdown}
      >
        <DialogTitle>Create Product Breakdown</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are all products ready for breakdown?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loadingBreakdown}>Cancel</Button>
          <Button onClick={() => createBreakdown(id)} disabled={loadingBreakdown}>
            Create Breakdown
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  )
}