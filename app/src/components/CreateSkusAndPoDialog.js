import React, { Fragment, useState } from "react";
import {
  Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle,
  CircularProgress,
  TextField,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import sendRequest from '../utils/sendRequest'

export default function CreateSkusAndPoDialog({ buttonLoading, setButtonLoading, id, isAts, addSnackbar, fetchPos }) {
  const [open, setOpen] = useState(false);
  const [loadingSkuPo, setLoadingSkuPo] = useState(false);
  const [poId, setPoId] = useState(0)

  const handleOpen = () => {
    setOpen(true);
  };

  const handleClose = () => {
    if (!loadingSkuPo) {
      setOpen(false);
    }
  };

  const handlePoIdChange = (e) => {
    let id = parseInt(e.target.value);
    if (id > 0) {
      setPoId(id);
    }
  }

  const createSkusAndPo = async (id) => {
    handleClose();
    setButtonLoading(true);
    setLoadingSkuPo(true);
    try {
      let response;
      if (!isAts) {
        if (poId === 0) {
          throw Error("Invalid Purchase Order ID.");
        }
        response = await sendRequest(
          `purchase-orders/${id}/create-skus-and-po-non-ats`, { po_id: poId }, "POST"
        );
      } else {
        response = await sendRequest(`purchase-orders/${id}/create-skus-and-po-ats`)
      }

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
        disabled={buttonLoading}
        onClick={handleOpen}
      >
        {loadingSkuPo ? <CircularProgress size={24} /> : <PlayArrowIcon color="success" />}
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        disableEscapeKeyDown={loadingSkuPo}
      >
        <DialogTitle>Create SKUs and PO</DialogTitle>
        {( isAts ) &&  (
          <DialogContent>
            <DialogContentText>
              Are all products finalized and ready to be uploaded?
            </DialogContentText>
          </DialogContent>
        )}
        {( !isAts ) && (
          <DialogContent>
            <DialogContentText>
              Please enter the ID of the purchase order in SellerCloud.
            </DialogContentText>
            <TextField
              required
              type="number"
              variant="standard"
              fullWidth
              onChange={handlePoIdChange}
            />
          </DialogContent>
        )}
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