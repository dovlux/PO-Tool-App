import { useState } from "react";
import { Button, CircularProgress, Stack } from "@mui/material";
import sendRequest from "../utils/sendRequest";
import { useAllContext } from "./Context";

export default function UpdateCacheButton({ row }) {
  const [updatingCache, setUpdatingCache] = useState(false);
  const { fetchCacheStatus, addSnackbar } = useAllContext();

  const updateCache = async (name) => {
    setUpdatingCache(true);
    try {
      let response = await sendRequest(
        `dev/cache/${name}/update`, null, 'GET'
      );
      fetchCacheStatus();
      addSnackbar(response.message);
    } catch (error) {
      addSnackbar(error.message, false);
    } finally {
      setUpdatingCache(false);
    }
  }

  return (
    (row.status !== "Updating...") &&
    <Stack alignContent='center' m={1}>
      <Button
        variant="contained"
        color="primary"
        disabled={updatingCache}
        onClick={() => updateCache(row.name.replace("_", "-"))}
      >
        {updatingCache ? <CircularProgress size={24} /> : 'Update'}
      </Button>
    </Stack>
  )
}