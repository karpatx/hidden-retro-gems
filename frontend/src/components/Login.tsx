import { useState } from 'react'
import {
  Container,
  Paper,
  TextInput,
  PasswordInput,
  Button,
  Title,
  Text,
  Alert,
  Stack
} from '@mantine/core'
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'

function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bejelentkezés sikertelen')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container size={420} my={40}>
      <Title ta="center" mb="md">
        Bejelentkezés
      </Title>
      <Text c="dimmed" size="sm" ta="center" mt={5} mb={30}>
        Jelentkezz be a fiókodba
      </Text>

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <form onSubmit={handleSubmit}>
          <Stack gap="md">
            {error && (
              <Alert color="red" title="Hiba">
                {error}
              </Alert>
            )}

            <TextInput
              label="Email"
              placeholder="ikarpati@gmail.com"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
            />

            <PasswordInput
              label="Jelszó"
              placeholder="Jelszavad"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <Button fullWidth mt="xl" type="submit" loading={loading}>
              Bejelentkezés
            </Button>
          </Stack>
        </form>
      </Paper>
    </Container>
  )
}

export default Login

