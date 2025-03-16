import dotenv from "dotenv";
// Load environment variables
dotenv.config();

export interface EnvConfig {
  PRIV_KEY_WALLET: string;
  INSTANT_NODES_HTTPS_URI: string;
  INSTANT_NODES_WSS_URI: string;
  HELIUS_HTTPS_URI: string;
  HELIUS_WSS_URI: string;
  VIBE_HTTPS_URI: string;
  VIBE_WSS_URI: string;
  HTTPS_URI: string;
  WSS_URI: string;
}

export function validateEnv(): EnvConfig {
  const requiredEnvVars = [
    "PRIV_KEY_WALLET",
    "INSTANT_NODES_HTTPS_URI",
    "INSTANT_NODES_WSS_URI",
    'HELIUS_HTTPS_URI',
    'HELIUS_WSS_URI',
    'VIBE_HTTPS_URI',
    'VIBE_WSS_URI',
    'HTTPS_URI',
    'HTTPS_URI'
  ] as const;

  const missingVars = requiredEnvVars.filter((envVar) => {
    if (envVar === "PRIV_KEY_WALLET" && !process.env[envVar]) {
      return false; // Allow PRIV_KEY_WALLET to be empty
    }
    return !process.env[envVar];
  });

  if (missingVars.length > 0) {
    throw new Error(`🚫 Missing required environment variables: ${missingVars.join(", ")}`);
  }

  const privKeyWallet = process.env.PRIV_KEY_WALLET;
  if (privKeyWallet && ![87, 88].includes(privKeyWallet.length)) {
    throw new Error(`🚫 PRIV_KEY_WALLET must be 87 or 88 characters long (got ${privKeyWallet.length})`);
  }

  const validateUrl = (envVar: string, protocol: string, checkApiKey: boolean = false) => {
    const value = process.env[envVar];
    if (!value) return;

    const url = new URL(value);
    if (value && url.protocol !== protocol) {
      throw new Error(`🚫 ${envVar} must start with ${protocol}`);
    }
    if (checkApiKey && value) {
      const apiKey = url.searchParams.get("api-key") || url.searchParams.get("api_key");
      if (!apiKey || apiKey.trim() === "") {
        throw new Error(`🚫 The 'api-key' parameter is missing or empty in the URL: ${value}`);
      }
    }
  };

  validateUrl("INSTANT_NODES_HTTPS_URI", "https:", true);
  validateUrl("INSTANT_NODES_WSS_URI", "wss:", true);
  validateUrl("HELIUS_HTTPS_URI", "https:", true);
  validateUrl("HELIUS_WSS_URI", "wss:", true);
  validateUrl("VIBE_HTTPS_URI", "http:", true);
  validateUrl("VIBE_WSS_URI", "ws:", true);

  // if (process.env.HELIUS_HTTPS_URI_TX?.includes("{function}")) {
  //   throw new Error("🚫 HELIUS_HTTPS_URI_TX contains {function}. Check your configuration.");
  // }

  return {
    PRIV_KEY_WALLET: process.env.PRIV_KEY_WALLET!,
    INSTANT_NODES_HTTPS_URI: process.env.INSTANT_NODES_HTTPS_URI!,
    INSTANT_NODES_WSS_URI: process.env.INSTANT_NODES_WSS_URI!,
    HELIUS_HTTPS_URI: process.env.HELIUS_HTTPS_URI!,
    HELIUS_WSS_URI: process.env.HELIUS_WSS_URI!,
    VIBE_HTTPS_URI: process.env.VIBE_HTTPS_URI!,
    VIBE_WSS_URI: process.env.VIBE_WSS_URI!,
    HTTPS_URI: process.env.HTTPS_URI!,
    WSS_URI: process.env.WSS_URI!,
  };
}