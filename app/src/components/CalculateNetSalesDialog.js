import React, { useState } from "react";
import { 
  Button, CircularProgress, Dialog, DialogTitle, DialogContent, DialogContentText,
  TextField, DialogActions
} from '@mui/material';
import sendRequest from '../utils/sendRequest'

export default function CalculateNetSalesDialog({ id, addSnackbar, fetchPos }) {
  const [loadingCalculate, setLoadingCalculate] = useState(false);
  const [open, setOpen] = useState(false);
  const [shippingFee, setShippingFee] = useState(0);
  const [customsFee, setCustomsFee] = useState(0);
  const [otherFee, setOtherFee] = useState(0);

  const handleOpen = () => {
    setOpen(true);
    setShippingFee(0);
    setCustomsFee(0);
    setOtherFee(0);
  };

  const handleClose = () => {
    if (!loadingCalculate) {
      setOpen(false);
    }
  };

  const handleShippingFeeChange = (e) => {
    let value = parseFloat(e.target.value);
    if (value >= 0) {
      setShippingFee(value);
    } else {
      setShippingFee(0);
      e.target.value = "";
    }
  }

  const handleCustomsFeeChange = (e) => {
    let value = parseFloat(e.target.value);
    if (value >= 0) {
      setCustomsFee(value);
    } else {
      setCustomsFee(0);
      e.target.value = "";
    }
  }

  const handleOtherFeeChange = (e) => {
    let value = parseFloat(e.target.value);
    if (value >= 0) {
      setOtherFee(value);
    } else {
      setOtherFee(0);
      e.target.value = "";
    }
  }

  const calculateNetSales = async (id, fees) => {
    console.log({fees: fees});
    setLoadingCalculate(true);
    try {
      let response = await sendRequest(`purchase-orders/${id}/calculate-net-sales`, fees, "POST");
      fetchPos();
      addSnackbar(response.message);
    } catch (error) {
      addSnackbar(error.message, false);
    } finally {
      setLoadingCalculate(false);
      handleClose();
    }
  }

  return (
    <>
      <Button variant="contained" color="success" onClick={handleOpen}>
        Net Sales
      </Button>
      <Dialog
        open={open}
        onClose={handleClose}
        disableEscapeKeyDown={loadingCalculate}
        PaperProps={{
          component: 'form',
          onSubmit: event => {
            event.preventDefault();
            const formData = new FormData(event.currentTarget);
            const formJson = Object.fromEntries(formData.entries());
            calculateNetSales(id, formJson);
          },
        }}
      >
        <DialogTitle>Additional Costs</DialogTitle>
        <DialogContent>
          <DialogContentText>Please enter all additional costs that apply (USD).</DialogContentText>
          <TextField
            autoFocus
            required
            margin="dense"
            id="shipping_fees"
            name="shipping_fees"
            label="Shipping Fees"
            type="number"
            fullWidth
            variant="standard"
            onChange={handleShippingFeeChange}
          />
          <TextField
            required
            margin="dense"
            id="customs_fees"
            name="customs_fees"
            label="Customs Fees"
            type="number"
            fullWidth
            variant="standard"
            onChange={handleCustomsFeeChange}
          />
          <TextField
            required
            margin="dense"
            id="other_fees"
            name="other_fees"
            label="Other Fees"
            type="number"
            fullWidth
            variant="standard"
            onChange={handleOtherFeeChange}
          />
          <div></div>
          <DialogContentText variant="h6">{`Total Fees: $${(shippingFee + customsFee + otherFee)}`}</DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loadingCalculate}>Cancel</Button>
          <Button type="submit" disabled={loadingCalculate}>
            {loadingCalculate ? <CircularProgress size={24} /> : 'Submit'}
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}