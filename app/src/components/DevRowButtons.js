import { Stack } from "@mui/material";
import ViewLogsDialog from "./ViewLogsDialog";
import ChangeStatusDialog from "./ChangeStatusDialog";

export default function DevRowButtons ({ row, addSnackbar, fetchPos }) {
  return (
    <Stack direction='row' alignContent='center' spacing={1} m={1}>
      <ViewLogsDialog
        row={row}
      />
      <ChangeStatusDialog 
        row={row}
        addSnackbar={addSnackbar}
        fetchPos={fetchPos}
      />
    </Stack>
  )
}