
/**
 * Check if the parsed data is a pool creation
 * Return the signature if it is, otherwise return false
 */

type ParsedData = {
  type: string;
  source: string;
  params: {
    result: {
      value: {
        logs?: string[];
        signature?: string;
      };
    };
  }; 
};

export function verify(parsedData: ParsedData): string | false {
  // Safely access the nested structure
  const logs = parsedData?.params?.result?.value?.logs;
  const signature = parsedData?.params?.result?.value?.signature;

  // Validate `logs` is an array and if we have a signtature
  if (!Array.isArray(logs) || !signature) return false;

  // Verify if this is a new pool creation
  const containsCreate = logs.some((log: string) => typeof log === "string" && log.includes("Program log: initialize2: InitializeInstruction2"));
  if (!containsCreate || typeof signature !== "string") return false;

  return signature;
}
