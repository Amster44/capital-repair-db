import React, { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TextField, Typography, Pagination, CircularProgress, Box } from '@mui/material';
import axios from 'axios';

const API_URL = 'http://62.113.36.101:5000/api';

export default function Companies() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    axios.get(API_URL + '/companies?page=' + page + '&search=' + search)
      .then(res => {
        setCompanies(res.data.companies);
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
      <Typography variant="h4" gutterBottom>Управляющие компании</Typography>
      <TextField
        label="Поиск по названию, ОГРН или телефону"
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
                  <TableCell>Название</TableCell>
                  <TableCell>ОГРН</TableCell>
                  <TableCell>Телефон</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Директор</TableCell>
                  <TableCell>Зданий</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {companies.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell>{c.name}</TableCell>
                    <TableCell>{c.ogrn}</TableCell>
                    <TableCell>{c.phone || '-'}</TableCell>
                    <TableCell>{c.email || '-'}</TableCell>
                    <TableCell>{c.director_name || '-'}</TableCell>
                    <TableCell>{c.buildings_count}</TableCell>
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
