import React, { Fragment, useState } from "react";
import {
  Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle,
  CircularProgress,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import sendRequest from '../utils/sendRequest'

export default function DeletePoDialog({ buttonLoading, setButtonLoading, id, addSnackbar, fetchPos }) {
  const [open, setOpen] = useState(false);
  const [loadingDelete, setLoadingDelete] = useState(false);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    if (!loadingDelete) {
      setOpen(false);
    }
  };

  const deletePurchaseOrder = async (id) => {
    handleClose();
    setButtonLoading(true);
    setLoadingDelete(true);
    try {
      let response = await sendRequest(`purchase-orders/${id}`, null, 'DELETE');
      fetchPos();
      addSnackbar(response.message);
    } catch (error) {
      addSnackbar(error.message, false);
    } finally {
      setButtonLoading(false);
      setLoadingDelete(false);
    }
  }

  return (
    <Fragment>
      <Button
        disabled={buttonLoading}
        onClick={handleOpen}
      >
        {loadingDelete ? <CircularProgress size={24} /> : <DeleteIcon color='error' />}
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        disableEscapeKeyDown={loadingDelete}
      >
        <DialogTitle>Delete PO Draft</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this PO? This action is irreversible!
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loadingDelete}>Cancel</Button>
          <Button onClick={() => deletePurchaseOrder(id)} disabled={loadingDelete}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  )
}