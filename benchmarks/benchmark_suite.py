"""Automated Performance and Accuracy Benchmark Suite for KTP Hotel OCR.

Measures end-to-end and component latencies (preprocessing, OCR, parsing, transformation),
calculates statistical percentiles (p50, p90, p95, p99), throughput (FPS),
tracks system memory RSS usage, and evaluates field extraction accuracy.
"""

import argparse
from dataclasses import asdict, dataclass
import json
import math
import os
import statistics
import time
from typing import Any, Dict, List
import psutil

from app.config import get_settings
from app.services.hotel_transformer import HotelCheckInTransformer
from app.services.ktp_parser import KTPParser
from app.services.ocr_engine import TesseractOCREngine
from app.services.preprocessor import ImagePreprocessor
from benchmarks.mock_generator import SyntheticKTPConfig, SyntheticKTPGenerator


@dataclass
class SampleBenchmarkResult:
    """Benchmark metrics for a single image evaluation."""
    sample_id: str
    preprocessing_ms: float
    ocr_ms: float
    parsing_ms: float
    transformation_ms: float
    total_ms: float
    ocr_confidence: float
    nik_matched: bool
    name_matched: bool
    gender_matched: bool


class BenchmarkSuite:
    """Orchestrates performance and accuracy benchmarking across diverse test scenarios."""

    def __init__(self, iterations: int = 5):
        self.iterations = iterations
        self.settings = get_settings()
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = TesseractOCREngine(
            tesseract_cmd=self.settings.TESSERACT_CMD,
            tessdata_prefix=self.settings.TESSDATA_PREFIX,
        )
        self.ktp_parser = KTPParser()
        self.transformer = HotelCheckInTransformer(min_adult_age=self.settings.MIN_ADULT_AGE)
        self.process = psutil.Process(os.getpid())

    def _build_test_scenarios(self) -> List[tuple[str, SyntheticKTPConfig]]:
        """Generates representative testing scenarios."""
        return [
            (
                "Standard Clean Adult",
                SyntheticKTPConfig(
                    nik="3171011505900001",
                    nama="BUDI SANTOSO",
                    jenis_kelamin="LAKI-LAKI",
                    tempat_lahir="JAKARTA",
                    tanggal_lahir="15-05-1990",
                ),
            ),
            (
                "Skewed Rotated (+3 deg)",
                SyntheticKTPConfig(
                    nik="3271012010850002",
                    nama="HENDRA WIJAYA",
                    jenis_kelamin="LAKI-LAKI",
                    tempat_lahir="BANDUNG",
                    tanggal_lahir="20-10-1985",
                    skew_angle=3.0,
                ),
            ),
            (
                "Noisy Camera Sensor",
                SyntheticKTPConfig(
                    nik="3374011203920003",
                    nama="AGUS SETIAWAN",
                    jenis_kelamin="LAKI-LAKI",
                    tempat_lahir="SEMARANG",
                    tanggal_lahir="12-03-1992",
                    add_noise=True,
                ),
            ),
            (
                "Female Guest (+40 Rule)",
                SyntheticKTPConfig(
                    nik="3578016512950004",  # Day 25 + 40 = 65
                    nama="DEWI LESTARI",
                    jenis_kelamin="PEREMPUAN",
                    tempat_lahir="SURABAYA",
                    tanggal_lahir="25-12-1995",
                ),
            ),
            (
                "Minor Guest (17yo)",
                SyntheticKTPConfig(
                    nik="5171011005090005",
                    nama="MADE ARYA",
                    jenis_kelamin="LAKI-LAKI",
                    tempat_lahir="DENPASAR",
                    tanggal_lahir="10-05-2009",
                ),
            ),
        ]

    def run(self) -> Dict[str, Any]:
        """Executes full benchmark suite across all scenarios and iterations."""
        scenarios = self._build_test_scenarios()
        results: List[SampleBenchmarkResult] = []

        initial_memory_mb = self.process.memory_info().rss / (1024 * 1024)

        print(f"\n{'='*78}")
        print(f"  KTP HOTEL CHECK-IN OCR BENCHMARK SUITE (v{self.settings.APP_VERSION})")
        print(f"  Scenarios: {len(scenarios)} | Iterations per scenario: {self.iterations}")
        print(f"  Tesseract Lang: {self.settings.OCR_LANG} | Engine Mode: {self.settings.OCR_OEM}")
        print(f"{'='*78}\n")

        for scenario_name, cfg in scenarios:
            img_bytes = SyntheticKTPGenerator.generate_image_bytes(cfg)

            for it in range(self.iterations):
                # 1. Preprocessing benchmark
                t0 = time.perf_counter()
                _, processed = self.preprocessor.preprocess(img_bytes)
                t_prep = (time.perf_counter() - t0) * 1000.0

                # 2. OCR benchmark
                t1 = time.perf_counter()
                ocr_res = self.ocr_engine.execute_ocr(processed)
                t_ocr = (time.perf_counter() - t1) * 1000.0

                # 3. Parsing benchmark
                t2 = time.perf_counter()
                ktp_data = self.ktp_parser.parse(ocr_res.raw_text)
                t_parse = (time.perf_counter() - t2) * 1000.0

                # 4. Transformation benchmark
                t3 = time.perf_counter()
                profile, _ = self.transformer.transform(ktp_data, ocr_res.average_confidence)
                t_trans = (time.perf_counter() - t3) * 1000.0

                total_ms = t_prep + t_ocr + t_parse + t_trans

                # Evaluate accuracy
                nik_match = cfg.nik == profile.identity_number
                name_match = cfg.nama.upper() == profile.guest_full_name.upper()
                gender_match = cfg.jenis_kelamin.upper() in (profile.gender.value.upper(), "LAKI-LAKI" if profile.gender.value == "MALE" else "PEREMPUAN")

                results.append(
                    SampleBenchmarkResult(
                        sample_id=f"{scenario_name} [#{it+1}]",
                        preprocessing_ms=round(t_prep, 2),
                        ocr_ms=round(t_ocr, 2),
                        parsing_ms=round(t_parse, 2),
                        transformation_ms=round(t_trans, 2),
                        total_ms=round(total_ms, 2),
                        ocr_confidence=ocr_res.average_confidence,
                        nik_matched=nik_match,
                        name_matched=name_match,
                        gender_matched=gender_match,
                    )
                )

        final_memory_mb = self.process.memory_info().rss / (1024 * 1024)

        # Statistical calculations
        total_latencies = [r.total_ms for r in results]
        prep_latencies = [r.preprocessing_ms for r in results]
        ocr_latencies = [r.ocr_ms for r in results]
        parse_latencies = [r.parsing_ms for r in results]
        trans_latencies = [r.transformation_ms for r in results]

        p50 = statistics.median(total_latencies)
        p90 = self._percentile(total_latencies, 90)
        p95 = self._percentile(total_latencies, 95)
        p99 = self._percentile(total_latencies, 99)
        mean_lat = statistics.mean(total_latencies)
        min_lat = min(total_latencies)
        max_lat = max(total_latencies)
        stdev_lat = statistics.stdev(total_latencies) if len(total_latencies) > 1 else 0.0

        nik_accuracy = sum(1 for r in results if r.nik_matched) / len(results) * 100.0
        name_accuracy = sum(1 for r in results if r.name_matched) / len(results) * 100.0
        gender_accuracy = sum(1 for r in results if r.gender_matched) / len(results) * 100.0
        avg_conf = sum(r.ocr_confidence for r in results) / len(results) * 100.0

        throughput_fps = 1000.0 / mean_lat if mean_lat > 0 else 0.0

        report = {
            "summary": {
                "total_runs": len(results),
                "throughput_req_per_sec": round(throughput_fps, 2),
                "memory_rss_start_mb": round(initial_memory_mb, 2),
                "memory_rss_end_mb": round(final_memory_mb, 2),
                "memory_rss_delta_mb": round(final_memory_mb - initial_memory_mb, 2),
            },
            "latency_stats_ms": {
                "mean": round(mean_lat, 2),
                "median_p50": round(p50, 2),
                "p90": round(p90, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2),
                "min": round(min_lat, 2),
                "max": round(max_lat, 2),
                "stdev": round(stdev_lat, 2),
            },
            "component_latency_breakdown_avg_ms": {
                "preprocessing": round(statistics.mean(prep_latencies), 2),
                "ocr_engine": round(statistics.mean(ocr_latencies), 2),
                "ktp_parsing": round(statistics.mean(parse_latencies), 2),
                "hotel_transformation": round(statistics.mean(trans_latencies), 2),
            },
            "accuracy_metrics": {
                "nik_extraction_accuracy_pct": round(nik_accuracy, 2),
                "name_extraction_accuracy_pct": round(name_accuracy, 2),
                "gender_extraction_accuracy_pct": round(gender_accuracy, 2),
                "average_ocr_confidence_pct": round(avg_conf, 2),
            },
            "raw_sample_runs": [asdict(r) for r in results],
        }

        self._print_formatted_summary(report)
        return report

    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """Calculates percentile from list of floats."""
        size = len(data)
        if size == 0:
            return 0.0
        sorted_data = sorted(data)
        idx = int(math.ceil((percentile / 100.0) * size)) - 1
        return sorted_data[max(0, min(idx, size - 1))]

    def _print_formatted_summary(self, report: Dict[str, Any]) -> None:
        """Prints a human-readable table summary."""
        lat = report["latency_stats_ms"]
        comp = report["component_latency_breakdown_avg_ms"]
        acc = report["accuracy_metrics"]
        summ = report["summary"]

        print(f"{'METRIC':<36} | {'VALUE':<18}")
        print(f"{'-'*36}-+-{'-'*18}")
        print(f"{'Total Benchmark Runs':<36} | {summ['total_runs']}")
        print(f"{'Throughput (Req/Sec)':<36} | {summ['throughput_req_per_sec']} req/s")
        print(f"{'Memory Delta (RSS)':<36} | {summ['memory_rss_delta_mb']} MB")
        print(f"{'-'*36}-+-{'-'*18}")
        print(f"{'Mean Latency':<36} | {lat['mean']} ms")
        print(f"{'Median Latency (p50)':<36} | {lat['median_p50']} ms")
        print(f"{'90th Percentile (p90)':<36} | {lat['p90']} ms")
        print(f"{'95th Percentile (p95)':<36} | {lat['p95']} ms")
        print(f"{'99th Percentile (p99)':<36} | {lat['p99']} ms")
        print(f"{'Min / Max Latency':<36} | {lat['min']} / {lat['max']} ms")
        print(f"{'-'*36}-+-{'-'*18}")
        print(f"{'-> Preprocessing (CLAHE, Deskew)':<36} | {comp['preprocessing']} ms")
        print(f"{'-> Tesseract OCR Engine':<36} | {comp['ocr_engine']} ms")
        print(f"{'-> KTP Field Regex Parsing':<36} | {comp['ktp_parsing']} ms")
        print(f"{'-> Hotel Profile Transformation':<36} | {comp['hotel_transformation']} ms")
        print(f"{'-'*36}-+-{'-'*18}")
        print(f"{'NIK Extraction Accuracy':<36} | {acc['nik_extraction_accuracy_pct']}%")
        print(f"{'Name Extraction Accuracy':<36} | {acc['name_extraction_accuracy_pct']}%")
        print(f"{'Gender Extraction Accuracy':<36} | {acc['gender_extraction_accuracy_pct']}%")
        print(f"{'Average OCR Confidence':<36} | {acc['average_ocr_confidence_pct']}%")
        print(f"{'='*57}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KTP OCR Benchmark Suite")
    parser.add_argument("--iterations", type=int, default=3, help="Number of iterations per scenario (default: 3)")
    parser.add_argument("--output", type=str, default=None, help="Save report to JSON file path")
    args = parser.parse_args()

    suite = BenchmarkSuite(iterations=args.iterations)
    result = suite.run()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"[+] Benchmark report saved to: {args.output}")
