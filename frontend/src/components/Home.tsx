import { Title, Text, Container, Grid, Paper } from '@mantine/core'

function Home() {
  return (
    <Container>
      <Title order={1} ta="center" mb="lg">
        Hidden Gem
      </Title>
      <Text ta="center" size="lg" mb="xl">
        Fedezd fel a rejtett játék gyöngyszemeit!
      </Text>

      <Grid gutter="md">
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Paper shadow="xs" p="md" radius="md" withBorder>
            <Title order={3} mb="sm">🎮 Széles választék</Title>
            <Text>
              Több mint 5000 kevésbé ismert játék konzolonként és platformonként.
            </Text>
          </Paper>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 4 }}>
          <Paper shadow="xs" p="md" radius="md" withBorder>
            <Title order={3} mb="sm">🔍 Keresés</Title>
            <Text>
              Találd meg a tökéletes játékot cím, platform vagy konzol alapján.
            </Text>
          </Paper>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 4 }}>
          <Paper shadow="xs" p="md" radius="md" withBorder>
            <Title order={3} mb="sm">💎 Felfedezés</Title>
            <Text>
              Ismerkedj meg új és izgalmas játékgépekkel, amelyek megérdemlik a figyelmet.
            </Text>
          </Paper>
        </Grid.Col>
      </Grid>
    </Container>
  )
}

export default Home

