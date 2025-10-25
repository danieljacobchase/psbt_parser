"""
PSBT Report - Format and display PSBT information in human-readable format
"""

class PSBTReport:
    """Formatter for displaying PSBT information."""

    @staticmethod
    def print_summary(psbt_info, recommended_fee_rates=None):
        """
        Print a human-readable summary of a PSBT.

        Args:
            psbt_info: PSBTInfo object with parsed transaction details
            recommended_fee_rates: Optional dict of recommended fee rates from mempool API
        """
        print("\n" + "="*60)
        print("PSBT SUMMARY")
        print("="*60)

        # PSBT Version
        print(f"\nPSBT Version: {psbt_info.version}")

        # Input breakdown
        print(f"\nInputs ({len(psbt_info.inputs)}):")
        for i, input_info in enumerate(psbt_info.inputs):
            print(f"  [{i}] {input_info.amount:,} sats | {input_info.address_type} | {input_info.script_type}")

        # Output breakdown
        print(f"\nOutputs ({len(psbt_info.outputs)}):")
        for i, output_info in enumerate(psbt_info.outputs):
            change_marker = " (change output)" if psbt_info.change_output[i] else ""
            print(f"  [{i}] {output_info.amount:,} sats | {output_info.address_type} | {output_info.script_type}{change_marker}")

        # Transaction Summary with fee assessment
        print(f"\nTransaction Summary:")
        print(f"  Total Input:  {psbt_info.total_input_amt:,} sats")
        print(f"  Total Output: {psbt_info.total_output_amt:,} sats")
        print(f"  Fee:          {psbt_info.fee_amt:,} sats")
        print(f"  Fee Rate:     ~{round(psbt_info.fee_rate)} sat/vB")

        # Fee assessment
        if recommended_fee_rates:
            minimum_fee = recommended_fee_rates.get("minimumFee", 1)
            economy_fee = recommended_fee_rates.get("economyFee", 1)
            hour_fee = recommended_fee_rates.get("hourFee", 1)
            half_hour_fee = recommended_fee_rates.get("halfHourFee", 1)
            fastest_fee = recommended_fee_rates.get("fastestFee", 1)

            if minimum_fee == economy_fee == hour_fee == half_hour_fee == fastest_fee == 1:
                print("  Assessment:   Mempool is empty - transaction should confirm in next block regardless of fee")
                if psbt_info.fee_rate > 2:
                    print("                Note: Supplied fee is excessive for current mempool conditions")
            elif psbt_info.fee_rate < minimum_fee:
                print("  Assessment:   Fee rate is too low")
            elif psbt_info.fee_rate < economy_fee:
                print("  Assessment:   Transaction could take several hours to days to confirm")
            elif psbt_info.fee_rate < hour_fee:
                print("  Assessment:   Transaction could take more than an hour to confirm")
            elif psbt_info.fee_rate < half_hour_fee:
                print("  Assessment:   Transaction should confirm between 30 minutes and an hour")
            elif psbt_info.fee_rate < fastest_fee:
                print("  Assessment:   Transaction should take less than 30 minutes to confirm")
            elif psbt_info.fee_rate <= 1.5 * fastest_fee:
                print("  Assessment:   Transaction should confirm in less than 10 minutes")
            elif psbt_info.fee_rate < 3 * fastest_fee:
                print("  Assessment:   Fee rate is high but tolerable")
            else:
                print("  Assessment:   Fee rate is excessive/wasteful")
        else:
            print("  Assessment:   Could not fetch recommended fee rates from mempool API")

        print("="*60 + "\n")
