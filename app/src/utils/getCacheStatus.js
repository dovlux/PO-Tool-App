import sendRequest from "./sendRequest";
import UpdateCacheButton from "../components/UpdateCacheButton";

export async function getCacheStatus() {
  const columns = [
    { field: 'name', headerName: 'Sheet Name', width: 200 },
    { field: 'status', headerName: 'Status', width: 150},
    { field: 'update_time', headerName: 'Last Updated', width: 200,
      valueGetter: (value) => new Date(value).toLocaleString(),
    },
    {
      field: 'update',
      headerName: 'Update',
      width: 200,
      sortable: false,
      headerAlign: 'center',
      renderCell: (params) => <UpdateCacheButton row={params.row} />
    }
  ];

  let data = await sendRequest('dev/cache/status');
  let rows = data.map((row, index) => ({ ...row, id: index }));

  return {
    columns: columns,
    rows: rows,
  }
}