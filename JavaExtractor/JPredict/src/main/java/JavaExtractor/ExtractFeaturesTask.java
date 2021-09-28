package JavaExtractor;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Callable;

import org.apache.commons.lang3.StringUtils;

import com.github.javaparser.ParseException;
import com.github.javaparser.ast.CompilationUnit;

import JavaExtractor.Common.CommandLineValues;
import JavaExtractor.Common.Common;
import JavaExtractor.FeaturesEntities.ProgramFeatures;

public class ExtractFeaturesTask implements Callable<Void> {
	CommandLineValues m_CommandLineValues;

	public ExtractFeaturesTask(CommandLineValues commandLineValues) {
		m_CommandLineValues = commandLineValues;
	}

	@Override
	public Void call() throws Exception {
		//System.err.println("Extracting file: " + filePath);
		process("");
		//System.err.println("Done with file: " + filePath);
		return null;
	}

	public String process(String code) {
		ArrayList<ProgramFeatures> features;
		try {
			features = extractSingleFile(code);
		} catch (ParseException | IOException e) {
			e.printStackTrace();
			return "";
		}
		if (features == null) {
			return "";
		}

		return featuresToString(features);
	}

	public ArrayList<ProgramFeatures> extractSingleFile(String code) throws ParseException, IOException {
		FeatureExtractor featureExtractor = new FeatureExtractor(m_CommandLineValues);

		ArrayList<ProgramFeatures> features = featureExtractor.extractFeatures(code);

		return features;
	}

	public String featuresToString(ArrayList<ProgramFeatures> features) {
		if (features == null || features.isEmpty()) {
			return Common.EmptyString;
		}

		List<String> methodsOutputs = new ArrayList<>();

		for (ProgramFeatures singleMethodfeatures : features) {
			StringBuilder builder = new StringBuilder();
			
			String toPrint = Common.EmptyString;
			toPrint = singleMethodfeatures.toString();
			if (m_CommandLineValues.PrettyPrint) {
				toPrint = toPrint.replace(" ", "\n\t");
			}
			builder.append(toPrint);
			

			methodsOutputs.add(builder.toString());

		}
		return StringUtils.join(methodsOutputs, "\n");
	}
}
