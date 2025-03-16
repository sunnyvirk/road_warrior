import axios from "axios";
import { config } from "./config";

// Local types
import {
  RugResponseExtended,
  NewTokenRecord,
} from "./types";

import {
  insertNewToken,
  selectTokenByNameAndCreator
} from './tracker/db';


export async function getRugCheckConfirmed(tokenMint: string): Promise<boolean> {
  const rugResponse = await axios.get<RugResponseExtended>("https://api.rugcheck.xyz/v1/tokens/" + tokenMint + "/report", {
    timeout: config.tx.get_timeout,
  });

  if (!rugResponse.data) return false;

  if (config.rug_check.verbose_log && config.rug_check.verbose_log === true) {
    console.log(rugResponse.data);
  }

  // Extract information
  const tokenReport: RugResponseExtended = rugResponse.data;
  const tokenCreator = tokenReport.creator ? tokenReport.creator : tokenMint;
  const {
    token,
    tokenMeta,
    totalLPProviders,
    totalMarketLiquidity,
    rugged: isRugged,
    score: rugScore,
  } = tokenReport;
  let topHolders = tokenReport.topHolders
  const {
    mintAuthority,
    freezeAuthority,
    isInitialized,
    supply,
    decimals,
  } = token;
  const {
    name: tokenName,
    symbol: tokenSymbol,
    mutable: tokenMutable,
  } = tokenMeta;

  const marketsLength = tokenReport.markets ? tokenReport.markets.length : 0;

  const rugRisks = tokenReport.risks
    ? tokenReport.risks
    : [
        {
          name: "Good",
          value: "",
          description: "",
          score: 0,
          level: "good",
        },
      ];

  // Get config
  const rugCheckConfig = config.rug_check;

  // Update topholders if liquidity pools are excluded
  if (rugCheckConfig.exclude_lp_from_topholders) {
    // local types
    type Market = {
      liquidityA?: string;
      liquidityB?: string;
    };

    const markets: Market[] | undefined = tokenReport.markets;
    if (markets) {
      // Safely extract liquidity addresses from markets
      const liquidityAddresses: string[] = (markets ?? [])
        .flatMap((market) => [market.liquidityA, market.liquidityB])
        .filter((address): address is string => !!address);

      // Filter out topHolders that match any of the liquidity addresses
      topHolders = topHolders.filter((holder) => !liquidityAddresses.includes(holder.address));
    }
  }

  
  const rugCheckLegacy = rugCheckConfig.legacy_not_allowed;

  const topHolder = topHolders.reduce((prev, current) => (prev.pct > current.pct ? prev : current), topHolders[0]);

  let insiderNetworkPercentage = 0;
  let insiderNetwork = 0;

  if (rugResponse.data.insiderNetworks) {
    insiderNetworkPercentage = Math.ceil((rugResponse.data.insiderNetworks[0].tokenAmount / rugResponse.data.token.supply) * 100);
    insiderNetwork = rugResponse.data.insiderNetworks[0].size;
  }

  // Set conditions
  const conditions = [
    {
      check: !rugCheckConfig.allow_graph_insiders && insiderNetworkPercentage > 50,
      message: `🚫 Graph insiders detected ${insiderNetworkPercentage}% sent to ${insiderNetwork} wallets`,
    },
    {
      check: rugCheckLegacy.includes("Low Liquidity") && totalMarketLiquidity < rugCheckConfig.min_total_market_Liquidity,
      message: `🚫 Low Liquidity ${totalMarketLiquidity} < ${rugCheckConfig.min_total_market_Liquidity}`,
    },
    {
      check: rugCheckLegacy.includes("Freeze Authority still enabled") && freezeAuthority !== null,
      message: "🚫 Freeze Authority still enabled",
    },
    {
      check: rugCheckLegacy.includes("Single holder ownership") && topHolders.some((holder) => holder.pct > 50),
      message: `🚫 Single holder ownership ${topHolder.pct}`,
    },
    {
      check: rugCheckLegacy.includes("High holder concentration") && topHolders.some((holder) => holder.pct > rugCheckConfig.max_alowed_pct_topholders),
      message: `🚫 High holder concentration ${topHolder.pct}`,
    },
    {
      check: rugCheckLegacy.includes("Large Amount of LP Unlocked"),
      message: "🚫 Large Amount of LP Unlocked",
    },
    {
      check: rugCheckLegacy.includes("Low amount of LP Providers") && totalLPProviders < rugCheckConfig.min_total_lp_providers,
      message: `🚫 Low amount of LP Providers ${totalLPProviders}`,
    },
    {
      check: !rugCheckConfig.allow_mint_authority && mintAuthority !== null,
      message: "🚫 Mint authority should be null",
    },
    {
      check: !rugCheckConfig.allow_not_initialized && !isInitialized,
      message: "🚫 Token is not initialized",
    },
    {
      check: !rugCheckConfig.allow_freeze_authority && freezeAuthority !== null,
      message: "🚫 Freeze authority should be null",
    },
    {
      check: !rugCheckConfig.allow_mutable && tokenMutable !== false,
      message: "🚫 Mutable should be false",
    },
    {
      check: !rugCheckConfig.allow_insider_topholders && topHolders.some((holder) => holder.insider),
      message: "🚫 Insider accounts should not be part of the top holders",
    },
    {
      check: totalLPProviders < rugCheckConfig.min_total_lp_providers,
      message: `🚫 Not enough LP Providers. ${totalLPProviders}`,
    },
    {
      check: marketsLength < rugCheckConfig.min_total_markets,
      message: `🚫 Not enough Markets. ${marketsLength}`,
    },
    {
      check: totalMarketLiquidity < rugCheckConfig.min_total_market_Liquidity,
      message: `🚫 Not enough Market Liquidity. ${totalMarketLiquidity}`,
    },
    {
      check: !rugCheckConfig.allow_rugged && isRugged, //true
      message: "🚫 Token is rugged",
    },
    {
      check: rugCheckConfig.block_symbols.includes(tokenSymbol),
      message: "🚫 Symbol is blocked",
    },
    {
      check: rugCheckConfig.block_names.includes(tokenName),
      message: "🚫 Name is blocked",
    },
    {
      check: rugScore > rugCheckConfig.max_score && rugCheckConfig.max_score !== 0,
      message: "🚫 Rug score to high.",
    },
  ];

  // If tracking duplicate tokens is enabled
  if (config.rug_check.block_returning_token_names || config.rug_check.block_returning_token_creators) {
    // Get duplicates based on token min and creator
    const duplicate = await selectTokenByNameAndCreator(tokenName, tokenCreator);

    // Verify if duplicate token or creator was returned
    if (duplicate.length !== 0) {
      if (config.rug_check.block_returning_token_names && duplicate.some((token) => token.name === tokenName)) {
        console.log("🚫 Token with this name was already created");
        return false;
      }
      if (config.rug_check.block_returning_token_creators && duplicate.some((token) => token.creator === tokenCreator)) {
        console.log("🚫 Token from this creator was already created");
        return false;
      }
    }
  }

  // Create new token record
  const newToken: NewTokenRecord = {
    time: Date.now(),
    mint: tokenMint,
    name: tokenName,
    creator: tokenCreator,
  };
  await insertNewToken(newToken).catch((err) => {
    if (config.rug_check.block_returning_token_names || config.rug_check.block_returning_token_creators) {
      console.log("⛔ Unable to store new token for tracking duplicate tokens: " + err);
    }
  });

  //Validate conditions
  for (const condition of conditions) {
    if (condition.check) {
      console.log(condition.message);
      return false;
    }
  }

  return true;
}