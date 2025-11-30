import { useState, useEffect } from 'react'
import {
  Container,
  Title,
  Grid,
  Card,
  Text,
  Badge,
  Stack,
  Group,
  LoadingOverlay,
  Anchor,
} from '@mantine/core'
import { useNavigate } from 'react-router-dom'
import { toSlug } from '../utils/slug'

interface Manufacturer {
  name: string
  platforms: string[]
  total_games: number
}

function Manufacturers() {
  const [manufacturers, setManufacturers] = useState<Manufacturer[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetchManufacturers()
  }, [])

  const fetchManufacturers = async () => {
    try {
      const response = await fetch('http://localhost:8000/manufacturers')
      const data = await response.json()
      setManufacturers(data.manufacturers)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching manufacturers:', error)
      setLoading(false)
    }
  }

  const getColorForManufacturer = (name: string): string => {
    const colors: { [key: string]: string } = {
      Nintendo: 'red',
      Sony: 'blue',
      Sega: 'teal',
      Microsoft: 'green',
      SNK: 'orange',
      NEC: 'purple',
      PC: 'grape',
      Commodore: 'cyan',
      Sinclair: 'yellow',
      'Pico-8': 'pink',
    }
    return colors[name] || 'gray'
  }

  return (
    <Container>
      <Title order={1} mb="lg">
        Gyártók
      </Title>

      <div style={{ position: 'relative' }}>
        <LoadingOverlay visible={loading} />
        <Grid gutter="md">
          {manufacturers.map((mfr) => (
            <Grid.Col key={mfr.name} span={{ base: 12, sm: 6, md: 4, lg: 3 }}>
              <Anchor
                onClick={() => navigate(`/manufacturer/${toSlug(mfr.name)}`)}
                underline="never"
              >
                <Card
                  shadow="sm"
                  padding="lg"
                  radius="md"
                  withBorder
                  style={{ cursor: 'pointer', height: '100%' }}
                  className="manufacturer-card"
                >
                  <Stack gap="xs">
                    <Group justify="space-between" mb="xs">
                      <Text fw={700} size="xl">
                        {mfr.name}
                      </Text>
                    </Group>

                    <Group gap="xs">
                      <Badge
                        variant="light"
                        color={getColorForManufacturer(mfr.name)}
                        size="lg"
                      >
                        {mfr.total_games} játék
                      </Badge>
                    </Group>

                    <Text size="sm" c="dimmed" mt="xs">
                      {mfr.platforms.length} platform
                    </Text>

                    <Group gap={4} mt="xs">
                      {mfr.platforms.slice(0, 3).map((platform) => (
                        <Badge
                          key={platform}
                          variant="outline"
                          size="xs"
                          color={getColorForManufacturer(mfr.name)}
                        >
                          {platform}
                        </Badge>
                      ))}
                      {mfr.platforms.length > 3 && (
                        <Badge variant="dot" size="xs" color="gray">
                          +{mfr.platforms.length - 3}
                        </Badge>
                      )}
                    </Group>
                  </Stack>
                </Card>
              </Anchor>
            </Grid.Col>
          ))}
        </Grid>
      </div>
    </Container>
  )
}

export default Manufacturers

