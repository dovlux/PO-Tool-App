import React, { Fragment, useState } from "react";
import {
  Button, TextField, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle,
  CircularProgress, FormControlLabel, Checkbox,
} from '@mui/material';
import sendRequest from '../utils/sendRequest'
import { useAllContext } from "./Context";

export default function CreatePoDialog() {
  const [open, setOpen] = useState(false);
  const [loadingCreate, setLoadingCreate] = useState(false);
  const [isAts, setIsAts] = useState(false);
  const { addSnackbar, fetchPos } = useAllContext();

  const handleOpen = () => {
    setOpen(true);
    setIsAts(false);
  };

  const handleClose = () => {
    if (!loadingCreate) {
      setOpen(false);
    }
  };

  const createPurchaseOrder = async (name, isAts) => {
    setLoadingCreate(true);
    try {
      await sendRequest('purchase-orders', { name: name, is_ats: isAts }, 'POST');
      fetchPos();
      addSnackbar("Creating Purchase Order...");
    } catch (error) {
      addSnackbar(error.message, false);
    } finally {
      setLoadingCreate(false);
      handleClose();
    }
  }

  return (
    <Fragment>
      <Button variant="contained" onClick={handleOpen}>
        Create Purchase Order
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        disableEscapeKeyDown={loadingCreate}
        PaperProps={{
          component: 'form',
          onSubmit: event => {
            event.preventDefault();
            const formData = new FormData(event.currentTarget);
            const formJson = Object.fromEntries(formData.entries());
            createPurchaseOrder(formJson.name, isAts);
          },
        }}
      >
        <DialogTitle>Create New PO Draft</DialogTitle>
        <DialogContent>
          <DialogContentText>Please enter the name of the Purchase Order</DialogContentText>
          <TextField
            autoFocus
            required
            margin="dense"
            id="name"
            name="name"
            label="PO Name"
            type="text"
            fullWidth
            variant="standard"
          />
          <div></div>
          <FormControlLabel
            control={
              <Checkbox
                checked={isAts} 
                onChange={(e) => setIsAts(e.target.checked)}
                name="is_ats"
                color="primary"
              />
            }
            label="ATS"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loadingCreate}>Cancel</Button>
          <Button type="submit" disabled={loadingCreate}>
            {loadingCreate ? <CircularProgress size={24} /> : 'Submit'}
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  )
}