import React, { Fragment, useState } from "react";
import {
  Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle,
  CircularProgress,
} from '@mui/material';
import UndoIcon from '@mui/icons-material/Undo';
import sendRequest from '../utils/sendRequest'

export default function UndoDialog({ buttonLoading, setButtonLoading, id, status, addSnackbar, fetchPos }) {
  const [open, setOpen] = useState(false);
  const [loadingUndo, setLoadingUndo] = useState(false);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    if (!loadingUndo) {
      setOpen(false);
    }
  };

  const undoPoStatus = async (id) => {
    handleClose();
    setButtonLoading(true);
    setLoadingUndo(true);
    try {
      let response = await sendRequest(`purchase-orders/${id}/undo-status`, null, "PUT");
      fetchPos();
      addSnackbar(response.message);
    } catch (error) {
      addSnackbar(error.message, false);
    } finally {
      setButtonLoading(false);
      setLoadingUndo(false);
    }
  }

  return (
    <Fragment>
      <Button
        disabled={buttonLoading}
        onClick={handleOpen}
      >
        {loadingUndo ? <CircularProgress size={24} /> : <UndoIcon color="primary" />}
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        disableEscapeKeyDown={loadingUndo}
      >
        <DialogTitle>Undo Recent Process</DialogTitle>
        <DialogContent>
          <DialogContentText>
            {`Are you sure you want to undo the latest process (${status})?`}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loadingUndo}>Cancel</Button>
          <Button color="warning" onClick={() => undoPoStatus(id)} disabled={loadingUndo}>
            {`Undo ${status}`}
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  )
}