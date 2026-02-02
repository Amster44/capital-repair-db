import React, { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TextField, Typography, Pagination, CircularProgress, Box } from '@mui/material';
import axios from 'axios';

const API_URL = 'http://62.113.36.101:5000/api';

export default function Buildings() {
  const [buildings, setBuildings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    axios.get(API_URL + '/buildings?page=' + page + '&search=' + search)
      .then(res => {
        setBuildings(res.data.buildings);
        setTotal(res.data.pages);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [page, search]);

  return (
    <>
      <Typography variant="h4" gutterBottom>Здания</Typography>
      <TextField
        label="Поиск по адресу или коду МКД"
        variant="outlined"
        fullWidth
        sx={{ mb: 2 }}
        value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
      />
      
      {loading ? <CircularProgress /> : (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>ID</TableCell>
                  <TableCell>Адрес</TableCell>
                  <TableCell>Код МКД</TableCell>
                  <TableCell>Площадь</TableCell>
                  <TableCell>Баланс ФКР</TableCell>
                  <TableCell>УК</TableCell>
                  <TableCell>Телефон</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {buildings.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell>{b.id}</TableCell>
                    <TableCell>{b.address}</TableCell>
                    <TableCell>{b.mkd_code}</TableCell>
                    <TableCell>{b.total_sq ? b.total_sq + ' м²' : '-'}</TableCell>
                    <TableCell>{b.overhaul_funds_balance || '-'}</TableCell>
                    <TableCell>{b.company_name || '-'}</TableCell>
                    <TableCell>{b.phone || '-'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
            <Pagination count={total} page={page} onChange={(e, p) => setPage(p)} color="primary" />
          </Box>
        </>
      )}
    </>
  );
}
