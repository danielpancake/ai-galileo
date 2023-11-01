use std::{
    fs::File,
    io::{BufWriter, Write},
    path::PathBuf,
    time::Duration,
};

use anyhow::{Context, Result};
use pyo3::prelude::*;
// use rodio::{
//     source::{Buffered, Source},
//     Decoder,
// };

#[derive(clap::Parser)]
struct Opts {
    audio: PathBuf,
    transcription: PathBuf,
}

#[derive(Debug, Clone)]
struct Segment {
    from: Duration,
    to: Duration,
    line: String,
}

impl std::str::FromStr for Segment {
    type Err = anyhow::Error;

    fn from_str(s: &str) -> std::result::Result<Self, Self::Err> {
        let s = s.strip_prefix('[').context("Missing `[`")?;

        let (time, line) = s.split_once(']').context("Missing closing `]`")?;

        let (from, tail) = time.split_once('s').context("Missing `s` for first time")?;
        let from: f64 = from
            .parse()
            .with_context(|| format!("when parsing '{}'", from))?;

        let (_, to) = tail.split_once(" -> ").context("Missing ` -> `")?;
        let to = to
            .strip_suffix('s')
            .context("Missing `s` for second time")?;
        let to: f64 = to
            .parse()
            .with_context(|| format!("when parsing '{}'", to))?;

        Ok(Self {
            from: Duration::from_secs_f64(from),
            to: Duration::from_secs_f64(to),
            line: line.trim().to_owned(),
        })
    }
}

fn main() -> Result<()> {
    let opts: Opts = clap::Parser::parse();

    std::fs::create_dir_all("out/audio/")?;

    pyo3::prepare_freethreaded_python();

    let transcription = std::fs::read_to_string(opts.transcription)?;
    // println!("Raw transcription:");
    // println!("{}", transcription);

    let mut ids_writer = BufWriter::new(File::create("out/ids.txt")?);

    let python_source = std::fs::read_to_string("main.py").context("when reading python source")?;
    Python::with_gil(|py| -> anyhow::Result<()> {
        let fun: Py<PyAny> = PyModule::from_code(py, &python_source, "", "")
            .context("when compiling python")?
            .getattr("cut_audio")?
            .into();

        for (i, line) in transcription.lines().enumerate() {
            let segment: Segment = line
                .parse()
                .with_context(|| format!("when parsing line\n{}", line))?;
            println!("Processing {:?}", segment);
            cut_audio(
                py,
                &fun,
                opts.audio
                    .as_os_str()
                    .to_str()
                    .context("failed to read audio path")?,
                &format!("out/audio/{:03}.mp3", i),
                segment.from,
                segment.to,
            )
            .context("when cutting audio")?;

            writeln!(&mut ids_writer, "{:03}|{}", i, segment.line)?;
        }

        Ok(())
    })?;

    Ok(())
}

fn cut_audio(
    py: Python,
    fun: &Py<PyAny>,
    source: &str,
    target: &str,
    from: Duration,
    to: Duration,
) -> Result<()> {
    fun.call1(py, (source, target, from.as_millis(), to.as_millis()))
        .context("when calling python")?;
    Ok(())
}
