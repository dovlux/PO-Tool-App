import React, { Fragment, useState } from "react";
import {
  Button, TextField, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle,
  CircularProgress, FormControlLabel, Checkbox, FormControl, InputLabel, Select, MenuItem,
  Stack
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import sendRequest from '../utils/sendRequest'

export default function CreatePoDialog({ addSnackbar, fetchPos }) {
  const [open, setOpen] = useState(false);
  const [loadingCreate, setLoadingCreate] = useState(false);
  const [isAts, setIsAts] = useState(false);
  const [currency, setCurrency] = useState("");

  const handleOpen = () => {
    setOpen(true);
    setIsAts(false);
    setCurrency("");
  };

  const handleClose = () => {
    if (!loadingCreate) {
      setOpen(false);
    }
  };

  const createPurchaseOrder = async (name, isAts, currency) => {
    setLoadingCreate(true);
    try {
      await sendRequest('purchase-orders', { name: name, is_ats: isAts, currency: currency }, 'POST');
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
      <Button onClick={handleOpen}>
        <AddIcon color="inherit" />
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
            createPurchaseOrder(formJson.name, isAts, currency);
          },
        }}
      >
        <DialogTitle>Create New PO Draft</DialogTitle>
        <DialogContent>
          <DialogContentText>Please enter the name and currency of the Purchase Order</DialogContentText>
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
          <Stack direction="row">
            <FormControlLabel
              control={
                <Checkbox
                  checked={!isAts} 
                  onChange={(e) => setIsAts(!e.target.checked)}
                  name="is_lux"
                  color="primary"
                />
              }
              label="LUX"
            />
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
          </Stack>
          <FormControl fullWidth variant="standard" margin="dense">
            <InputLabel id="currency-label">Currency</InputLabel>
            <Select
              labelId="currency-label"
              id="currency"
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              label="Currency"
            >
              <MenuItem value={'USD'}>USD</MenuItem>
              <MenuItem value={'EUR'}>EUR</MenuItem>
              <MenuItem value={'GBP'}>GBP</MenuItem>
              <MenuItem value={'JPY'}>JPY</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loadingCreate}>Cancel</Button>
          <Button type="submit" disabled={loadingCreate || currency === ''}>
            {loadingCreate ? <CircularProgress size={24} /> : 'Submit'}
          </Button>
        </DialogActions>
      </Dialog>
    </Fragment>
  )
}