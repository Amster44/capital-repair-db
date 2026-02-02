import React, { useState, useEffect } from 'react';
import { Grid, Card, CardContent, Typography, CircularProgress } from '@mui/material';
import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API_URL}/stats`)
      .then(res => {
        setStats(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <CircularProgress />;
  if (!stats) return <Typography>Ошибка загрузки данных</Typography>;

  const cards = [
    { title: 'Зданий', value: stats.buildings, color: '#1976d2' },
    { title: 'Управляющих компаний', value: stats.companies, color: '#2e7d32' },
    { title: 'С телефонами', value: stats.with_phone, color: '#ed6c02' },
    { title: 'С email', value: stats.with_email, color: '#9c27b0' },
    { title: 'Связей дом-УК', value: stats.linked, color: '#d32f2f' },
  ];

  return (
    <>
      <Typography variant="h4" gutterBottom>Статистика</Typography>
      <Grid container spacing={3}>
        {cards.map((card, idx) => (
          <Grid item xs={12} sm={6} md={4} key={idx}>
            <Card sx={{ backgroundColor: card.color, color: 'white' }}>
              <CardContent>
                <Typography variant="h3" align="center">{card.value?.toLocaleString() || 0}</Typography>
                <Typography variant="h6" align="center">{card.title}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </>
  );
}
