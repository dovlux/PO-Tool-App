import React, { Fragment, useState } from "react";
import {
  Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle,
  CircularProgress,
} from '@mui/material';
import sendRequest from '../utils/sendRequest'

export default function CreateSkusAndPoDialog({ buttonLoading, setButtonLoading, id, addSnackbar, fetchPos }) {
  const [open, setOpen] = useState(false);
  const [loadingSkuPo, setLoadingSkuPo] = useState(false);

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    if (!loadingSkuPo) {
      setOpen(false);
    }
  };

  const createSkusAndPo = async (id) => {
    handleClose();
    setButtonLoading(true);
    setLoadingSkuPo(true);
    try {
      let response = await sendRequest(`purchase-orders/${id}/create-skus-and-po`);
      fetchPos();
      addSnackbar(response.message);
    } catch (error) {
      addSnackbar(error.message, false);
    } finally {
      setButtonLoading(false);
      setLoadingSkuPo(false);
    }
  }

  return (
    <Fragment>
      <Button
        variant="contained"
        color="success"
        disabled={buttonLoading}
        onClick={handleOpen}
      >
        {loadingSkuPo ? <CircularProgress size={24} /> : 'Create SKUs and PO'}
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        disableEscapeKeyDown={loadingSkuPo}
      >
        <DialogTitle>Create SKUs and PO</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are all products finalized and ready to be uploaded?
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loadingSkuPo}>Cancel</Button>
          <Button onClick={() => createSkusAndPo(id)} disabled={loadingSkuPo}>
            Create SKUs and PO
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  )
}