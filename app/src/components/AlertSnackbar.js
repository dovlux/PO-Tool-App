import React from "react";
import { Snackbar, Alert } from '@mui/material';

export default function AlertSnackbar({ snackbars, setSnackbars }) {
  const handleClose = (id, reason) => {
    if (reason === 'clickaway') return;
    setSnackbars((prev) => prev.filter((snackbar) => snackbar.id !== id));
  };

  return (
    <div>
      {snackbars.map((snackbar, index) => (
        <Snackbar
          key={snackbar.id}
          open={true}
          autoHideDuration={snackbar.ms}
          onClose={(e, reason) => handleClose(snackbar.id, reason)}
          TransitionProps={{ onExited: () => handleClose(snackbar.id) }}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          sx={{ mb: (index * 7 + 1), mr: 4 }}
        >
          <Alert severity={snackbar.severity} variant="filled" sx={{ width: '100%' }}>
            {snackbar.message}
          </Alert>
        </Snackbar>
      ))}
    </div>
  )
}