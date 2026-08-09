#include "rampNode.h"

MObject rampNode::inDoubleArray;
MObject rampNode::inFloatArray;
MObject rampNode::inFloat;
MObject rampNode::aRamp;
MObject rampNode::oldMin;
MObject rampNode::oldMax;
MObject rampNode::Min;
MObject rampNode::Max;
MObject rampNode::outValue;
MObject rampNode::outFloat;

void *rampNode::creator()
{
	return new rampNode;
}

MStatus rampNode::initialize()
{
	MStatus stat;

	MFnTypedAttribute attrType;
	MFnNumericAttribute attNum;

	//// in Array float ////
	inFloatArray = attrType.create("floatMap", "floatMap", MFnData::kFloatArray, &stat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = addAttribute(inFloatArray);
	CHECK_MSTATUS_AND_RETURN_IT(stat);

	//// in Array double ////
	inDoubleArray = attrType.create("doubleMap", "doubleMap", MFnData::kDoubleArray, &stat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = addAttribute(inDoubleArray);
	CHECK_MSTATUS_AND_RETURN_IT(stat);

	//// curve ramp ///
	aRamp = MRampAttribute::createCurveRamp("Ramp", "Ramp");
	stat = addAttribute(aRamp);
	CHECK_MSTATUS_AND_RETURN_IT(stat);

	////// oldMin attribute ////////
	oldMin = attNum.create("oldMin", "oldMin", MFnNumericData::kDouble, 0.0, &stat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	CHECK_MSTATUS(attNum.setKeyable(true));
	stat = addAttribute(oldMin);
	CHECK_MSTATUS_AND_RETURN_IT(stat);

	////// oldMax attribute ////////
	oldMax = attNum.create("oldMax", "oldMax", MFnNumericData::kDouble, 0.0, &stat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	CHECK_MSTATUS(attNum.setKeyable(true));
	stat = addAttribute(oldMax);
	CHECK_MSTATUS_AND_RETURN_IT(stat);

	////// Min attribute ////////
	Min = attNum.create("Min", "Min", MFnNumericData::kDouble, 0.0, &stat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	CHECK_MSTATUS(attNum.setKeyable(true));
	stat = addAttribute(Min);
	CHECK_MSTATUS_AND_RETURN_IT(stat);

	////// Max attribute ////////
	Max = attNum.create("Max", "Max", MFnNumericData::kDouble, 0.0, &stat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	CHECK_MSTATUS(attNum.setKeyable(true));
	stat = addAttribute(Max);
	CHECK_MSTATUS_AND_RETURN_IT(stat);

	//// out Array double ////
	outValue = attrType.create("outValDbl", "outValDbl", MFnData::kDoubleArray, &stat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = addAttribute(outValue);
	CHECK_MSTATUS_AND_RETURN_IT(stat);

	//// out Array double ////
	outFloat = attrType.create("outValFl", "outValFl", MFnData::kFloatArray, &stat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = addAttribute(outFloat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);

	stat = attributeAffects(inDoubleArray, outValue);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = attributeAffects(inFloatArray, outValue);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = attributeAffects(aRamp, outValue);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = attributeAffects(oldMin, outValue);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = attributeAffects(oldMax, outValue);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = attributeAffects(Min, outValue);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = attributeAffects(Max, outValue);
	CHECK_MSTATUS_AND_RETURN_IT(stat);

	stat = attributeAffects(inDoubleArray, outFloat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = attributeAffects(inFloatArray, outFloat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = attributeAffects(aRamp, outFloat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = attributeAffects(oldMin, outFloat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = attributeAffects(oldMax, outFloat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = attributeAffects(Min, outFloat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);
	stat = attributeAffects(Max, outFloat);
	CHECK_MSTATUS_AND_RETURN_IT(stat);

	return MS::kSuccess;
}

MStatus rampNode::compute(const MPlug &plug, MDataBlock &data)
{
	MStatus stat;

	if (plug == outValue || plug == outFloat)
	{
		// 初始化ramp
		MRampAttribute curveAttribute(thisMObject(), aRamp, &stat);
		CHECK_MSTATUS_AND_RETURN_IT(stat);

		// 获取输入数组
		MDoubleArray inMDoubleArray;

		// 检查是双精度数组还是浮点数组输入
		MPlug doubleInputPlug(thisMObject(), inDoubleArray);
		MPlug floatInputPlug(thisMObject(), inFloatArray);

		if (doubleInputPlug.isConnected())
		{
			// 处理双精度数组输入
			MObject MdblArray = data.inputValue(inDoubleArray, &stat).data();
			CHECK_MSTATUS_AND_RETURN_IT(stat);
			MFnDoubleArrayData fnDoubleArray(MdblArray, &stat);
			CHECK_MSTATUS_AND_RETURN_IT(stat);
			inMDoubleArray = fnDoubleArray.array();
		}
		else if (floatInputPlug.isConnected())
		{
			// 处理浮点数组输入
			MObject MflArray = data.inputValue(inFloatArray, &stat).data();
			CHECK_MSTATUS_AND_RETURN_IT(stat);
			MFnFloatArrayData fnFloatArray(MflArray, &stat);
			CHECK_MSTATUS_AND_RETURN_IT(stat);
			MFloatArray inMFloatArray = fnFloatArray.array();

			// 转换为双精度数组以便统一处理
			int floatLen = inMFloatArray.length();
			for (int i = 0; i < floatLen; i++)
			{
				inMDoubleArray.append(static_cast<double>(inMFloatArray[i]));
			}
		}
		else
		{
			// 没有输入连接，返回空数组
			MDoubleArray emptyDoubleArray;
			MFloatArray emptyFloatArray;

			MDataHandle outMDoubleMapHandle = data.outputValue(outValue, &stat);
			CHECK_MSTATUS_AND_RETURN_IT(stat);

			MDataHandle outMapFlHandle = data.outputValue(outFloat, &stat);
			CHECK_MSTATUS_AND_RETURN_IT(stat);

			MFnDoubleArrayData fnOutArrayData;
			MFnFloatArrayData fnOutFlArrayData;

			MObject OutMObjDoubleArray = fnOutArrayData.create(emptyDoubleArray, &stat);
			CHECK_MSTATUS_AND_RETURN_IT(stat);

			MObject OutMObjFloatArray = fnOutFlArrayData.create(emptyFloatArray, &stat);
			CHECK_MSTATUS_AND_RETURN_IT(stat);

			stat = outMDoubleMapHandle.set(OutMObjDoubleArray);
			CHECK_MSTATUS_AND_RETURN_IT(stat);

			stat = outMapFlHandle.set(OutMObjFloatArray);
			CHECK_MSTATUS_AND_RETURN_IT(stat);

			stat = data.setClean(plug);
			CHECK_MSTATUS_AND_RETURN_IT(stat);

			return MS::kSuccess;
		}

		MDoubleArray outMDoubleArray;
		MFloatArray outMFloatArray;

		double inOldMin = data.inputValue(oldMin, &stat).asDouble();
		CHECK_MSTATUS_AND_RETURN_IT(stat);
		double inOldMax = data.inputValue(oldMax, &stat).asDouble();
		CHECK_MSTATUS_AND_RETURN_IT(stat);
		double inMin = data.inputValue(Min, &stat).asDouble();
		CHECK_MSTATUS_AND_RETURN_IT(stat);
		double inMax = data.inputValue(Max, &stat).asDouble();
		CHECK_MSTATUS_AND_RETURN_IT(stat);

		int len = inMDoubleArray.length();

		// 检查除零情况
		if (fabs(inOldMax - inOldMin) < 1e-10 || fabs(inMax - inMin) < 1e-10)
		{
			// 处理除零情况 - 使用默认值或报错
			for (int i = 0; i < len; i++)
			{
				outMDoubleArray.append(inMin);
				outMFloatArray.append(static_cast<float>(inMin));
			}
		}
		else
		{
			for (int i = 0; i < len; i++)
			{
				// 首先进行范围映射
				double normalizedInput = (inMDoubleArray[i] - inOldMin) / (inOldMax - inOldMin);
				double mappedValue = inMin + normalizedInput * (inMax - inMin);

				// 然后应用ramp曲线
				float rampValue;
				float normalizedMappedValue = (mappedValue - inMin) / (inMax - inMin); // 归一化到0-1范围
				curveAttribute.getValueAtPosition(normalizedMappedValue, rampValue);

				// 将ramp值映射回目标范围
				double finalVal = inMin + rampValue * (inMax - inMin);

				outMDoubleArray.append(finalVal);
				outMFloatArray.append(static_cast<float>(finalVal));
			}
		}

		// 设置输出
		MDataHandle outMDoubleMapHandle = data.outputValue(outValue, &stat);
		CHECK_MSTATUS_AND_RETURN_IT(stat);

		MDataHandle outMapFlHandle = data.outputValue(outFloat, &stat);
		CHECK_MSTATUS_AND_RETURN_IT(stat);

		MFnDoubleArrayData fnOutArrayData;
		MFnFloatArrayData fnOutFlArrayData;

		MObject OutMObjDoubleArray = fnOutArrayData.create(outMDoubleArray, &stat);
		CHECK_MSTATUS_AND_RETURN_IT(stat);

		MObject OutMObjFloatArray = fnOutFlArrayData.create(outMFloatArray, &stat);
		CHECK_MSTATUS_AND_RETURN_IT(stat);

		stat = outMDoubleMapHandle.set(OutMObjDoubleArray);
		CHECK_MSTATUS_AND_RETURN_IT(stat);

		stat = outMapFlHandle.set(OutMObjFloatArray);
		CHECK_MSTATUS_AND_RETURN_IT(stat);

		stat = data.setClean(plug);
		CHECK_MSTATUS_AND_RETURN_IT(stat);
	}
	else
	{
		return MS::kUnknownParameter;
	}
	return MS::kSuccess;
}