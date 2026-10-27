import { BrowserProvider, Contract } from 'ethers'
import ProjectRegistryArtifact from './ProjectRegistry.json'

export const CONTRACT_ADDRESS =
  '0x5FbDB2315678afecb367f032d93F642f64180aa3'

export const LOCAL_CHAIN_ID = 31337n

type EthereumProvider = {
  request: (args: {
    method: string
    params?: unknown[]
  }) => Promise<unknown>
}

declare global {
  interface Window {
    ethereum?: EthereumProvider
  }
}

export async function connectWallet() {
  if (!window.ethereum) {
    throw new Error(
      'MetaMask was not detected. Please install or enable the MetaMask extension.'
    )
  }

  const provider = new BrowserProvider(window.ethereum as never)

  await provider.send('eth_requestAccounts', [])

  const network = await provider.getNetwork()

  if (network.chainId !== LOCAL_CHAIN_ID) {
    throw new Error(
      'Please switch MetaMask to the local Hardhat network (chain ID 31337).'
    )
  }

  const signer = await provider.getSigner()

  const contract = new Contract(
    CONTRACT_ADDRESS,
    ProjectRegistryArtifact,
    signer
  )

  return {
    account: await signer.getAddress(),
    contract,
  }
}

export async function fingerprintFile(file: File): Promise<string> {
  const fileBytes = await file.arrayBuffer()
  const hash = await crypto.subtle.digest('SHA-256', fileBytes)

  const hex = Array.from(new Uint8Array(hash))
    .map(byte => byte.toString(16).padStart(2, '0'))
    .join('')

  return `0x${hex}`
}

export async function verifyRegisteredProject(fingerprint: string) {
  const { contract } = await connectWallet()

  const [isRegistered, owner, timestamp] =
    await contract.verifyProject(fingerprint)

  return {
    isRegistered: Boolean(isRegistered),
    owner: String(owner),
    timestamp: Number(timestamp),
  }
}