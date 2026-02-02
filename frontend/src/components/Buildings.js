import React, { useState, useEffect } from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TextField, Typography, Pagination, CircularProgress, Box, Grid, Select, MenuItem, FormControl, InputLabel, TableSortLabel, Chip, FormControlLabel, Checkbox } from '@mui/material';
import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

// Функция для нормализации телефонов
const formatPhone = (phone) => {
  if (!phone) return '-';
  // Убираем все кроме цифр
  const digits = phone.replace(/\D/g, '');
  // Форматируем в +7 (XXX) XXX-XX-XX
  if (digits.length === 11 && digits[0] === '7') {
    return `+7 (${digits.slice(1,4)}) ${digits.slice(4,7)}-${digits.slice(7,9)}-${digits.slice(9,11)}`;
  }
  if (digits.length === 10) {
    return `+7 (${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6,8)}-${digits.slice(8,10)}`;
  }
  return phone; // Возвращаем как есть, если не подходит формат
};

export default function Buildings() {
  const [buildings, setBuildings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [accountType, setAccountType] = useState('SPEC'); // По умолчанию только спецсчета
  const [minBalance, setMinBalance] = useState('0'); // Показываем все дома
  const [replacementYears, setReplacementYears] = useState([]); // Годы замены лифтов (массив)
  const [regions, setRegions] = useState([]);
  const [selectedRegion, setSelectedRegion] = useState('');
  const [sortBy, setSortBy] = useState('balance'); // balance, address, lifts, date
  const [sortOrder, setSortOrder] = useState('desc'); // asc или desc
  const [hasLifts, setHasLifts] = useState(true); // Только дома с лифтами

  // Загрузка списка регионов
  useEffect(() => {
    axios.get(`${API_URL}/regions`)
      .then(res => setRegions(res.data.regions))
      .catch(err => console.error(err));
  }, []);

  // Функция сортировки
  const handleSort = (column) => {
    if (sortBy === column) {
      // Меняем направление сортировки
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // Новая колонка, сортируем по убыванию
      setSortBy(column);
      setSortOrder('desc');
    }
    setPage(1); // Сбрасываем на первую страницу
  };

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({
      page,
      search,
      account_type: accountType,
      min_balance: minBalance,
      replacement_year: replacementYears.join(','), // Передаем годы через запятую
      region: selectedRegion,
      sort_by: sortBy,
      sort_order: sortOrder,
      has_lifts: hasLifts ? 'true' : 'false'
    });

    axios.get(`${API_URL}/buildings?${params}`)
      .then(res => {
        setBuildings(res.data.buildings);
        setTotal(res.data.pages);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [page, search, accountType, minBalance, replacementYears, selectedRegion, sortBy, sortOrder, hasLifts]);

  return (
    <>
      <Typography variant="h4" gutterBottom>Целевые здания для продажи лифтов</Typography>

      {selectedRegion && (
        <Box sx={{ mb: 2 }}>
          <Chip
            label={`Регион: ${selectedRegion}`}
            onDelete={() => setSelectedRegion('')}
            color="primary"
          />
        </Box>
      )}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <TextField
            label="Поиск по адресу или коду МКД"
            variant="outlined"
            fullWidth
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </Grid>

        <Grid item xs={12} md={2}>
          <FormControl fullWidth>
            <InputLabel>Регион</InputLabel>
            <Select value={selectedRegion} label="Регион" onChange={(e) => { setSelectedRegion(e.target.value); setPage(1); }}>
              <MenuItem value="">Все регионы</MenuItem>
              {regions.map((r, idx) => (
                <MenuItem key={idx} value={r.region}>{r.region}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={2}>
          <FormControl fullWidth>
            <InputLabel>Тип счета</InputLabel>
            <Select value={accountType} label="Тип счета" onChange={(e) => { setAccountType(e.target.value); setPage(1); }}>
              <MenuItem value="SPEC">Спецсчет (УК/ТСЖ/ЖСК)</MenuItem>
              <MenuItem value="REGOP">Регоператор</MenuItem>
              <MenuItem value="">Все</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={2}>
          <TextField
            label="Мин. баланс (тыс. руб)"
            variant="outlined"
            fullWidth
            type="number"
            value={minBalance}
            onChange={(e) => { setMinBalance(e.target.value); setPage(1); }}
          />
        </Grid>

        <Grid item xs={12} md={2}>
          <FormControl fullWidth>
            <InputLabel>Год замены лифтов</InputLabel>
            <Select
              multiple
              value={replacementYears}
              label="Год замены лифтов"
              onChange={(e) => { setReplacementYears(e.target.value); setPage(1); }}
              renderValue={(selected) => selected.length === 0 ? 'Все' : selected.join(', ')}
            >
              {(() => {
                const currentYear = new Date().getFullYear();
                const years = [];
                for (let y = currentYear - 5; y <= currentYear + 15; y++) {
                  years.push(<MenuItem key={y} value={y.toString()}>{y}</MenuItem>);
                }
                return years;
              })()}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={2}>
          <FormControlLabel
            control={
              <Checkbox
                checked={hasLifts}
                onChange={(e) => { setHasLifts(e.target.checked); setPage(1); }}
                color="primary"
              />
            }
            label="Только с лифтами"
          />
        </Grid>
      </Grid>

      {loading ? <CircularProgress /> : (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>
                    <TableSortLabel
                      active={sortBy === 'address'}
                      direction={sortBy === 'address' ? sortOrder : 'asc'}
                      onClick={() => handleSort('address')}
                    >
                      <strong>Адрес</strong>
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={sortBy === 'balance'}
                      direction={sortBy === 'balance' ? sortOrder : 'desc'}
                      onClick={() => handleSort('balance')}
                    >
                      <strong>Баланс ФКР (тыс. руб)</strong>
                    </TableSortLabel>
                  </TableCell>
                  <TableCell><strong>Тип счета</strong></TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={sortBy === 'lifts'}
                      direction={sortBy === 'lifts' ? sortOrder : 'desc'}
                      onClick={() => handleSort('lifts')}
                    >
                      <strong>Лифтов</strong>
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>
                    <TableSortLabel
                      active={sortBy === 'date'}
                      direction={sortBy === 'date' ? sortOrder : 'asc'}
                      onClick={() => handleSort('date')}
                    >
                      <strong>Срок замены</strong>
                    </TableSortLabel>
                  </TableCell>
                  <TableCell><strong>УК</strong></TableCell>
                  <TableCell><strong>Директор</strong></TableCell>
                  <TableCell><strong>Телефон</strong></TableCell>
                  <TableCell><strong>Email</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {buildings.map((b) => (
                  <TableRow key={b.id}>
                    <TableCell>
                      {b.region && <div style={{fontSize: '0.75rem', color: '#666'}}>{b.region}</div>}
                      {b.address}
                    </TableCell>
                    <TableCell><strong>{Number(b.overhaul_funds_balance || 0).toLocaleString('ru-RU')}</strong></TableCell>
                    <TableCell>{
                      b.spec_account_owner_type === 'UK' ? 'УК' :
                      b.spec_account_owner_type === 'TSJ' ? 'ТСЖ' :
                      b.spec_account_owner_type === 'JSK' ? 'ЖСК' :
                      'Регоператор'
                    }</TableCell>
                    <TableCell>{b.lifts_count || 0}</TableCell>
                    <TableCell>{b.nearest_replacement ? new Date(b.nearest_replacement).toLocaleDateString('ru-RU') : '-'}</TableCell>
                    <TableCell>{b.company_name || '-'}</TableCell>
                    <TableCell>{b.director_name || '-'}</TableCell>
                    <TableCell><a href={`tel:${b.phone}`}>{formatPhone(b.phone)}</a></TableCell>
                    <TableCell><a href={`mailto:${b.email}`}>{b.email || '-'}</a></TableCell>
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
