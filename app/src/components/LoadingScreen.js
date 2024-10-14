import { Backdrop, CircularProgress, Typography, Stack } from "@mui/material";

export default function LoadingScreen({ loading }) {
  return (
    <Backdrop open={loading} sx={(theme) => ({ color: '#fff', zIndex: theme.zIndex.drawer + 1})}>
      <Stack spacing={2} sx={{ justifyContent: 'center', alignItems: 'center' }} >
        <CircularProgress color="inherit" />
        <Typography>Loading...</Typography>
      </Stack>
    </Backdrop>
  )
}