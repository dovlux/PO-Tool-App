import { Backdrop, CircularProgress, Typography, Stack } from "@mui/material";
import { useAllContext } from "./Context";

export default function LoadingScreen() {
  const { loading } = useAllContext();
  
  return (
    <Backdrop open={loading} sx={(theme) => ({ color: '#fff', zIndex: theme.zIndex.drawer + 1})}>
      <Stack spacing={2} sx={{ justifyContent: 'center', alignItems: 'center' }} >
        <CircularProgress color="inherit" />
        <Typography>Loading...</Typography>
      </Stack>
    </Backdrop>
  )
}