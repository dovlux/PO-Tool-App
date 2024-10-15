import React, { useState } from "react";
import { Button, CircularProgress } from '@mui/material';
import sendRequest from '../utils/sendRequest'

export default function CalculateNetSalesDialog({ buttonLoading, setButtonLoading, id, addSnackbar, fetchPos }) {
  const [loadingCalculate, setLoadingCalculate] = useState(false);

  const calculateNetSales = async (id) => {
    setButtonLoading(true);
    setLoadingCalculate(true);
    try {
      let response = await sendRequest(`purchase-orders/${id}/calculate-net-sales`);
      fetchPos();
      addSnackbar(response.message);
    } catch (error) {
      addSnackbar(error.message, false);
    } finally {
      setButtonLoading(false);
      setLoadingCalculate(false);
    }
  }

  return (
    <Button
      variant="contained"
      color="success"
      disabled={buttonLoading}
      onClick={() => calculateNetSales(id)}
    >
      {loadingCalculate ? <CircularProgress size={24} /> : 'Calculate Net Sales'}
    </Button>
  )
}